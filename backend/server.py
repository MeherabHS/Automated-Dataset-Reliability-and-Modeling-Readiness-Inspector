from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
import pandas as pd
import numpy as np
import io
import csv
import json
import math
import textwrap
import warnings as py_warnings
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import os

from audit_engine import run_audit, sanitize as engine_sanitize

app = FastAPI(title="Automated Dataset Reliability and Modeling Readiness Inspector")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────────
# Scoring constants (Phase 5 spec-aligned)
# ────────────────────────────────────────────────

# Score band thresholds (score → label, checked highest-first)
SCORE_BANDS = [
    (85, "Ready"),
    (70, "Acceptable with preprocessing"),
    (50, "Needs preprocessing"),
    (0,  "High risk"),
]

MAX_PREVIEW_ROWS = 50
MAX_PARSE_PREVIEW_ROWS = 25
MAX_FILE_MB = 50
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024

# Allowed CSV MIME types (browsers vary significantly)
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/csv",
    "text/plain",
    "application/vnd.ms-excel",   # Some browsers send this for CSV
    "application/octet-stream",   # Fallback for unknown binary uploads
    "",                           # Occasionally empty from certain OS/browsers
}

ENCODING_FALLBACK_CHAIN = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

# Sniffer sample size (bytes)
DELIMITER_SNIFF_BYTES = 8192

# Bad-line threshold: if more than this % of rows are malformed, error out
BAD_LINE_THRESHOLD_PCT = 50.0


# ────────────────────────────────────────────────
# Parse error codes
# ────────────────────────────────────────────────
class ParseError(Exception):
    """Structured parse error with code, message, and hint."""
    def __init__(self, code: str, message: str, hint: str = ""):
        self.code = code
        self.message = message
        self.hint = hint
        super().__init__(message)


def _parse_error_response(code: str, message: str, hint: str = "", status_code: int = 422):
    return JSONResponse(
        status_code=status_code,
        content={"parse_error": True, "code": code, "message": message, "hint": hint},
    )


# ────────────────────────────────────────────────
# Ingestion helpers
# ────────────────────────────────────────────────
def validate_file_extension(filename: str) -> None:
    """Raise ParseError if filename doesn't end in .csv (case-insensitive)."""
    if not filename:
        raise ParseError(
            code="missing_filename",
            message="No filename was provided.",
            hint="Ensure your file has a .csv extension before uploading.",
        )
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext != "csv":
        raise ParseError(
            code="unsupported_file_type",
            message=f"File type '.{ext}' is not supported. Only CSV files are accepted.",
            hint="Save your data as a .csv file and try again. Excel (.xlsx) and other formats are not supported.",
        )


def detect_encoding(raw_bytes: bytes) -> str:
    """Try each encoding in the fallback chain; return first that succeeds."""
    for enc in ENCODING_FALLBACK_CHAIN:
        try:
            raw_bytes.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    raise ParseError(
        code="encoding_error",
        message="The file encoding could not be determined. None of the standard encodings (UTF-8, Latin-1) worked.",
        hint="Re-save the file as UTF-8 in your spreadsheet application and try again.",
    )


def detect_delimiter(text_sample: str) -> str:
    """Use csv.Sniffer to detect delimiter; fallback to comma."""
    try:
        dialect = csv.Sniffer().sniff(text_sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def parse_csv_bytes(
    raw_bytes: bytes,
    filename: str,
) -> Dict[str, Any]:
    """
    Core parsing logic.
    Returns a dict with: meta, preview, warnings, df (internal use).
    Raises ParseError for structured failures.
    """
    # 1. Detect encoding
    encoding = detect_encoding(raw_bytes)

    # 2. Decode
    try:
        text = raw_bytes.decode(encoding)
    except Exception as exc:
        raise ParseError(
            code="encoding_error",
            message=f"Failed to decode the file using {encoding}: {exc}",
            hint="Re-save the file as UTF-8 CSV and try again.",
        )

    if not text.strip():
        raise ParseError(
            code="empty_file",
            message="The uploaded file is empty.",
            hint="Ensure the CSV contains at least a header row and one data row.",
        )

    # 3. Detect delimiter on a sample
    sample = text[:DELIMITER_SNIFF_BYTES]
    delimiter = detect_delimiter(sample)

    # 4. Parse with pandas — capture bad-line warnings
    warnings_list: List[str] = []
    bad_line_count = 0

    # Count total lines for bad-line ratio check (excluding blank)
    all_lines = [ln for ln in text.splitlines() if ln.strip()]
    total_lines = max(len(all_lines) - 1, 0)  # subtract header

    # Build a bad-lines counter handler
    bad_lines_seen = []

    def _bad_line_handler(bad_line):
        bad_lines_seen.append(bad_line)
        return None  # skip the line

    try:
        # Use dtype=str so we preserve raw values exactly (no coercion)
        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            dtype=str,
            keep_default_na=False,   # keep "" as "" rather than NaN initially
            na_values=["", "NA", "N/A", "null", "NULL", "None", "NaN", "nan"],
            on_bad_lines="warn",
            encoding_errors="replace",
        )
    except pd.errors.EmptyDataError:
        raise ParseError(
            code="empty_file",
            message="The file contains no parseable data.",
            hint="Ensure the CSV has a header row followed by at least one data row.",
        )
    except pd.errors.ParserError as exc:
        raise ParseError(
            code="malformed_csv",
            message=f"The CSV structure could not be parsed: {str(exc)[:200]}",
            hint="Check for unescaped quotes, mixed delimiters, or missing fields. Open the file in a text editor to inspect.",
        )
    except Exception as exc:
        raise ParseError(
            code="parse_failed",
            message=f"An unexpected error occurred while parsing: {str(exc)[:200]}",
            hint="Verify the file is a well-formed CSV and try again.",
        )

    # 5. Validate parsed result
    if df.shape[1] == 0:
        raise ParseError(
            code="no_columns",
            message="No columns were detected in the CSV.",
            hint=f"Check that the file uses '{delimiter}' as its delimiter and has a header row.",
        )

    if len(df) == 0:
        raise ParseError(
            code="no_data_rows",
            message="The CSV has column headers but no data rows.",
            hint="Add at least one data row below the header and re-upload.",
        )

    # 6. Warn if delimiter was not comma
    if delimiter != ",":
        warnings_list.append(
            f"Non-standard delimiter detected: '{delimiter}'. "
            f"The file was parsed using this delimiter automatically."
        )

    # 7. Warn if encoding was not utf-8
    if encoding not in ("utf-8", "utf-8-sig"):
        warnings_list.append(
            f"Encoding detected as '{encoding}' (not UTF-8). "
            f"Consider re-saving as UTF-8 to avoid potential character issues."
        )

    # 8. Warn about bad lines
    # pandas 'warn' mode prints to stderr; we can't easily capture count
    # so we cross-check approximate row count vs expected
    expected_rows = max(total_lines, 0)
    actual_rows = len(df)
    skipped_estimate = max(expected_rows - actual_rows, 0)
    if skipped_estimate > 0:
        bad_pct = (skipped_estimate / max(expected_rows, 1)) * 100
        if bad_pct > BAD_LINE_THRESHOLD_PCT:
            raise ParseError(
                code="malformed_csv",
                message=f"More than {BAD_LINE_THRESHOLD_PCT:.0f}% of rows appear malformed ({skipped_estimate} of ~{expected_rows} rows could not be parsed).",
                hint="Check for inconsistent column counts, unescaped commas inside fields, or incorrect line endings.",
            )
        warnings_list.append(
            f"~{skipped_estimate} malformed row(s) were skipped during parsing."
        )

    # 9. Build preview (raw strings, replace NaN with None)
    preview_df = df.head(MAX_PARSE_PREVIEW_ROWS)
    preview_records = preview_df.where(pd.notnull(preview_df), None).to_dict(orient="records")

    # 10. Build column info (name + sample values from string column)
    column_info = []
    for col in df.columns:
        series = df[col]
        # Sample up to 3 non-null values
        samples = series.dropna().head(3).tolist()
        column_info.append({
            "name": col,
            "sample_values": samples,
        })

    meta = {
        "filename": filename,
        "rows": len(df),
        "cols": df.shape[1],
        "column_names": df.columns.tolist(),
        "encoding": encoding,
        "delimiter": delimiter,
        "preview_rows_shown": len(preview_records),
    }

    return {
        "meta": meta,
        "preview": preview_records,
        "column_info": column_info,
        "warnings": warnings_list,
        "df": df,  # internal — not serialized in API response
    }


# Helper utilities
# ────────────────────────────────────────────────
def safe_float(val):
    """Convert to float, handle NaN/Inf for JSON serialization."""
    if val is None:
        return None
    try:
        v = float(val)
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 4)
    except Exception:
        return None


def sanitize_for_json(obj):
    """Recursively convert NaN/Inf floats and numpy types for JSON compliance."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, np.floating):
        v = float(obj)
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 4)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    return obj


def infer_dtype_label(series: pd.Series) -> str:
    dtype = str(series.dtype)
    if dtype.startswith("int"):
        return "integer"
    elif dtype.startswith("float"):
        return "float"
    elif dtype == "bool":
        return "boolean"
    elif dtype == "object":
        # Try numeric coercion
        converted = pd.to_numeric(series.dropna(), errors="coerce")
        if converted.notna().mean() > 0.9:
            return "numeric-like (stored as string)"
        return "string"
    elif "datetime" in dtype:
        return "datetime"
    return dtype


def has_dtype_mismatch(series: pd.Series) -> bool:
    """Flag object columns that are mostly numeric values stored as strings."""
    if series.dtype != object:
        return False
    non_null = series.dropna()
    if len(non_null) == 0:
        return False
    converted = pd.to_numeric(non_null, errors="coerce")
    return converted.notna().mean() > 0.5


# ────────────────────────────────────────────────
# Audit modules
# ────────────────────────────────────────────────
def audit_schema(df: pd.DataFrame) -> dict:
    columns = []
    mismatch_warnings = []
    for col in df.columns:
        series = df[col]
        dtype_label = infer_dtype_label(series)
        null_count = int(series.isna().sum())
        null_pct = safe_float(null_count / len(df) * 100) if len(df) > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))
        mismatch = has_dtype_mismatch(series)
        if mismatch:
            mismatch_warnings.append(col)
        columns.append({
            "column": col,
            "dtype": dtype_label,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "dtype_mismatch": mismatch,
        })
    return {"columns": columns, "mismatch_warnings": mismatch_warnings}


def audit_missingness(df: pd.DataFrame) -> dict:
    total_cells = int(df.size)
    total_missing = int(df.isna().sum().sum())
    rows_with_missing = int(df.isna().any(axis=1).sum())
    missing_pct_total = safe_float(total_missing / total_cells * 100) if total_cells > 0 else 0.0

    per_column = []
    for col in df.columns:
        missing = int(df[col].isna().sum())
        if missing > 0:
            per_column.append({
                "column": col,
                "missing_count": missing,
                "missing_pct": safe_float(missing / len(df) * 100),
            })
    per_column.sort(key=lambda x: x["missing_count"], reverse=True)

    return {
        "total_cells": total_cells,
        "total_missing": total_missing,
        "missing_pct_total": missing_pct_total,
        "rows_with_missing": rows_with_missing,
        "rows_with_missing_pct": safe_float(rows_with_missing / len(df) * 100) if len(df) > 0 else 0.0,
        "per_column": per_column,
    }


def audit_duplicates(df: pd.DataFrame) -> dict:
    dup_count = int(df.duplicated().sum())
    total_rows = len(df)
    dup_pct = safe_float(dup_count / total_rows * 100) if total_rows > 0 else 0.0

    if dup_pct is None or dup_pct < 1:
        risk_label = "Low"
    elif dup_pct < 10:
        risk_label = "Moderate"
    else:
        risk_label = "High"

    return {
        "duplicate_row_count": dup_count,
        "duplicate_pct": dup_pct,
        "risk_label": risk_label,
    }


def audit_outliers(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    results = []
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 4:
            continue
        Q1 = safe_float(series.quantile(0.25))
        Q3 = safe_float(series.quantile(0.75))
        if Q1 is None or Q3 is None:
            continue
        IQR = round(Q3 - Q1, 4)
        lower = round(Q1 - 1.5 * IQR, 4)
        upper = round(Q3 + 1.5 * IQR, 4)
        outlier_mask = (series < lower) | (series > upper)
        outlier_count = int(outlier_mask.sum())
        outlier_pct = safe_float(outlier_count / len(series) * 100)
        results.append({
            "column": col,
            "Q1": Q1,
            "Q3": Q3,
            "IQR": IQR,
            "lower_bound": lower,
            "upper_bound": upper,
            "outlier_count": outlier_count,
            "outlier_pct": outlier_pct,
        })
    return {"numeric_columns": results}


def audit_class_imbalance(df: pd.DataFrame, target_col: Optional[str]) -> dict:
    if not target_col or target_col not in df.columns:
        return {"target_col": None, "class_distribution": [], "severity": "N/A", "error": "No target column selected"}

    series = df[target_col].dropna()
    value_counts = series.value_counts()
    total = len(series)

    if total == 0:
        return {"target_col": target_col, "class_distribution": [], "severity": "N/A", "error": "Column is empty"}

    distribution = [
        {
            "class": str(cls),
            "count": int(cnt),
            "pct": safe_float(cnt / total * 100),
        }
        for cls, cnt in value_counts.items()
    ]

    n_classes = len(distribution)
    if n_classes == 0:
        severity = "N/A"
    elif n_classes == 1:
        severity = "Severe"
    else:
        max_pct = distribution[0]["pct"] or 0
        min_pct = distribution[-1]["pct"] or 0
        ratio = max_pct / min_pct if min_pct > 0 else float("inf")
        if ratio < 1.5:
            severity = "Balanced"
        elif ratio < 3:
            severity = "Mild Imbalance"
        elif ratio < 10:
            severity = "Moderate Imbalance"
        else:
            severity = "Severe Imbalance"

    return {
        "target_col": target_col,
        "class_distribution": distribution,
        "severity": severity,
    }


def audit_leakage(df: pd.DataFrame) -> dict:
    flagged = []
    for col in df.columns:
        col_lower = col.lower()
        matched_keywords = [kw for kw in LEAKAGE_KEYWORDS if kw in col_lower]
        if matched_keywords:
            flagged.append({"column": col, "matched_keywords": matched_keywords})
    return {"flagged_columns": flagged, "flag_count": len(flagged)}


def _score_band(score: float) -> str:
    """Map numeric score to human-readable score band."""
    for threshold, label in SCORE_BANDS:
        if score >= threshold:
            return label
    return "High risk"


def _penalty_entry(check: str, penalty: int, rule: str) -> dict:
    """Construct a standardised penalty record."""
    return {"check": check, "penalty": penalty, "rule": rule}


def _na_entry(check: str, reason: str) -> dict:
    """Construct a standardised not-applicable record."""
    return {"check": check, "reason": reason}


def _build_explanation(score: float, band: str, penalties: list, not_applicable: list) -> str:
    """
    Generate a concise, transparent one-paragraph explanation.
    Reads naturally and is suitable for display in the UI or the text report.
    """
    total_deducted = sum(p["penalty"] for p in penalties)
    n_issues = len(penalties)
    n_na = len(not_applicable)

    if n_issues == 0 and n_na == 0:
        return (
            f"The dataset scored {score:.0f}/100 ({band}). "
            "No issues were detected across all evaluated checks. "
            "The dataset appears suitable for modeling without significant preprocessing."
        )

    parts = [f"The dataset scored {score:.0f}/100 ({band})."]

    if n_issues == 0:
        parts.append("No penalties were applied.")
    else:
        issue_word = "issue" if n_issues == 1 else "issues"
        parts.append(
            f"{n_issues} {issue_word} reduced the score by {total_deducted} "
            f"point{'s' if total_deducted != 1 else ''} in total."
        )
        # List the top penalties concisely
        summary = "; ".join(
            f"{p['check']} (\u2212{p['penalty']})" for p in penalties
        )
        parts.append(f"Applied penalties: {summary}.")

    if n_na > 0:
        na_names = ", ".join(c["check"] for c in not_applicable)
        plural = "checks" if n_na > 1 else "check"
        parts.append(
            f"{n_na} {plural} could not be evaluated ({na_names}) "
            "and did not affect the score."
        )

    return " ".join(parts)


def compute_readiness_score(
    schema: dict,
    missingness: dict,
    duplicates: dict,
    outliers: dict,
    imbalance: dict,
    leakage: dict,
) -> dict:
    """
    Phase 5 scoring engine.

    Starts at 100 and subtracts deterministic rule-based penalties.
    Each check either contributes a penalty (with a clear rule string)
    or is recorded as not-applicable.

    Returns: score, score_band, penalties, not_applicable, explanation.
    """
    score: float = 100.0
    penalties: list = []
    not_applicable: list = []

    # ── 7. Basic schema quality ─────────────────────────────────────
    # Checked first — catastrophic schema failures dominate the score.
    if not schema.get("applicable", True):
        reason = schema.get("reason", "Unknown schema error")
        if "empty" in reason.lower():
            score -= 40
            penalties.append(_penalty_entry(
                "Basic schema quality", 40, "Empty dataset — no rows to inspect"
            ))
        else:
            score -= 40
            penalties.append(_penalty_entry(
                "Basic schema quality", 40, "Zero-column or zero-row dataset"
            ))
    else:
        # Zero-row / zero-column (edge case from schema metadata)
        if schema.get("row_count", 1) == 0 or schema.get("column_count", 1) == 0:
            score -= 40
            penalties.append(_penalty_entry(
                "Basic schema quality", 40, "Dataset has zero rows or zero columns"
            ))

        # Missing (unnamed / blank) header names
        columns = schema.get("columns", [])
        missing_header_cols = [
            c for c in columns
            if not str(c.get("name", "")).strip()
            or str(c.get("name", "")).strip().lower().startswith("unnamed")
        ]
        if missing_header_cols:
            score -= 10
            penalties.append(_penalty_entry(
                "Basic schema quality", 10,
                f"{len(missing_header_cols)} column(s) have missing or unnamed headers"
            ))

    # ── 1. Missingness ──────────────────────────────────────────────
    if not missingness.get("applicable", True):
        not_applicable.append(_na_entry("Missingness", missingness.get("reason", "Not applicable")))
    else:
        pct = missingness.get("missing_pct_overall") or 0.0
        if pct <= 1.0:
            pen = 0
        elif pct <= 5.0:
            pen = 5
        elif pct <= 10.0:
            pen = 10
        else:
            pen = 20

        if pen > 0:
            score -= pen
            penalties.append(_penalty_entry(
                "Missingness", pen,
                f"{pct:.1f}% of cells are missing "
                f"({'≤5%' if pct <= 5 else '≤10%' if pct <= 10 else '>10%'} band)"
            ))

    # ── 2. Duplicates ───────────────────────────────────────────────
    if not duplicates.get("applicable", True):
        not_applicable.append(_na_entry("Duplicates", duplicates.get("reason", "Not applicable")))
    else:
        pct = duplicates.get("duplicate_pct") or 0.0
        if pct == 0.0:
            pen = 0
        elif pct <= 1.0:
            pen = 5
        elif pct <= 3.0:
            pen = 10
        else:
            pen = 15

        if pen > 0:
            score -= pen
            penalties.append(_penalty_entry(
                "Duplicates", pen,
                f"{pct:.1f}% of rows are exact duplicates "
                f"({'≤1%' if pct <= 1 else '≤3%' if pct <= 3 else '>3%'} band)"
            ))

    # ── 3. Datatype anomalies ───────────────────────────────────────
    if not schema.get("applicable", True):
        not_applicable.append(_na_entry(
            "Datatype anomalies", "Schema module not applicable"
        ))
    else:
        n_mismatches = len(schema.get("mismatch_columns", []))
        if n_mismatches == 0:
            pen = 0
        elif n_mismatches <= 2:
            pen = 5
        elif n_mismatches <= 5:
            pen = 10
        else:
            pen = 15

        if pen > 0:
            score -= pen
            cols_str = ", ".join(schema.get("mismatch_columns", []))
            penalties.append(_penalty_entry(
                "Datatype anomalies", pen,
                f"{n_mismatches} column(s) have type-mismatch warnings: {cols_str}"
            ))

    # ── 4. Outliers ─────────────────────────────────────────────────
    if not outliers.get("applicable", True):
        not_applicable.append(_na_entry("Outliers", outliers.get("reason", "No numeric columns")))
    else:
        applicable_cols = [
            c for c in outliers.get("numeric_columns", [])
            if c.get("applicable", True)
        ]
        if not applicable_cols:
            not_applicable.append(_na_entry(
                "Outliers",
                "No numeric columns had sufficient data for IQR analysis"
            ))
        else:
            # Rule: any column above 20% → -10; any column above 10% → -5; else 0
            max_pct = max((c.get("outlier_pct") or 0.0) for c in applicable_cols)
            worst_col = next(
                c["column"] for c in applicable_cols
                if (c.get("outlier_pct") or 0.0) == max_pct
            )
            if max_pct > 20.0:
                pen = 10
                score -= pen
                penalties.append(_penalty_entry(
                    "Outliers", pen,
                    f"Column '{worst_col}' has {max_pct:.1f}% outliers (>20% threshold)"
                ))
            elif max_pct > 10.0:
                pen = 5
                score -= pen
                penalties.append(_penalty_entry(
                    "Outliers", pen,
                    f"Column '{worst_col}' has {max_pct:.1f}% outliers (>10% threshold)"
                ))
            # else: max_pct ≤ 10% → no penalty

    # ── 5. Class imbalance ──────────────────────────────────────────
    if not imbalance.get("applicable", True):
        not_applicable.append(_na_entry(
            "Class imbalance", imbalance.get("reason", "Not applicable")
        ))
    else:
        label = imbalance.get("imbalance_label", "")
        if label == "Balanced":
            pen = 0
        elif label == "Moderate imbalance":
            pen = 5
        elif label == "Severe imbalance":
            pen = 10
        else:
            pen = 0

        if pen > 0:
            score -= pen
            target = imbalance.get("target_col", "selected column")
            ratio = imbalance.get("majority_to_minority_ratio")
            ratio_str = f" (ratio {ratio:.1f}x)" if ratio else ""
            penalties.append(_penalty_entry(
                "Class imbalance", pen,
                f"'{target}' shows {label.lower()}{ratio_str}"
            ))

    # ── 6. Leakage-risk columns ─────────────────────────────────────
    if not leakage.get("applicable", True):
        not_applicable.append(_na_entry("Leakage risk", leakage.get("reason", "Not applicable")))
    else:
        flag_count = leakage.get("flag_count", 0)
        if flag_count >= 1:
            score -= 10
            flagged_names = ", ".join(
                f["column"] for f in leakage.get("flagged_columns", [])
            )
            penalties.append(_penalty_entry(
                "Leakage risk", 10,
                f"{flag_count} column(s) contain leakage-risk keywords: {flagged_names}"
            ))

    # ── Final score ─────────────────────────────────────────────────
    score = max(0.0, round(score, 1))
    band = _score_band(score)
    explanation = _build_explanation(score, band, penalties, not_applicable)

    return {
        "score": score,
        "score_band": band,
        "penalties": penalties,
        "not_applicable": not_applicable,
        "explanation": explanation,
    }


# ─────────────────────────────────────────────────────────────────
# Phase 6 — Report generator constants and helpers
# ─────────────────────────────────────────────────────────────────

_REPORT_WIDTH = 72
_MAJOR_SEP    = "=" * _REPORT_WIDTH
_SECTION_SEP  = "-" * _REPORT_WIDTH
_LBL_WIDTH    = 24  # label column width in key-value lines


def _kv(label: str, value, width: int = _LBL_WIDTH) -> str:
    """Return an aligned key: value line."""
    return f"  {label + ':':<{width}} {value}"


def _bullet(text: str, indent: int = 2) -> str:
    """Return a bullet-list item, wrapping long lines."""
    prefix = " " * indent + "- "
    subsequent = " " * (indent + 2)
    return textwrap.fill(
        text,
        width=_REPORT_WIDTH,
        initial_indent=prefix,
        subsequent_indent=subsequent,
    )


def _wrap_paragraph(text: str, indent: int = 2) -> str:
    """Wrap a long paragraph with consistent indentation."""
    return textwrap.fill(
        text,
        width=_REPORT_WIDTH,
        initial_indent=" " * indent,
        subsequent_indent=" " * indent,
    )


def _section_header(number: int, title: str) -> list:
    return [_SECTION_SEP, f"  {number}. {title}", _SECTION_SEP, ""]


def _na_block(reason: str) -> list:
    return [f"  Not applicable: {reason}", ""]


# ─────────────────────────────────────────────────────────────────
# Section builders
# ─────────────────────────────────────────────────────────────────

def _section_overview(meta: dict, imbalance: dict) -> list:
    rows    = meta.get("rows", 0)
    cols    = meta.get("cols", 0)
    fname   = meta.get("filename", "N/A")
    enc     = meta.get("encoding", "N/A")
    delim   = meta.get("delimiter", ",")
    target  = imbalance.get("target_col") or "Not selected"
    col_names = meta.get("column_names", [])

    lines = _section_header(1, "DATASET OVERVIEW")
    lines += [
        _kv("Filename",          fname),
        _kv("Rows",              f"{rows:,}"),
        _kv("Columns",           cols),
        _kv("Target Column",     target),
        _kv("Encoding",          enc),
        _kv("Delimiter",         repr(delim)),
        "",
    ]

    if col_names:
        lines.append("  Column names:")
        # wrap long column lists at report width
        col_str = ", ".join(col_names)
        for chunk_line in textwrap.wrap(col_str, width=_REPORT_WIDTH - 4,
                                        initial_indent="    ",
                                        subsequent_indent="    "):
            lines.append(chunk_line)
        lines.append("")

    return lines


def _section_schema(schema: dict) -> list:
    lines = _section_header(2, "SCHEMA DIAGNOSTICS")

    if not schema.get("applicable", True):
        return lines + _na_block(schema.get("reason", "Schema check not applicable"))

    lines += [
        _kv("Total Columns",     schema.get("column_count", "N/A")),
        _kv("Total Rows",        f"{schema.get('row_count', 0):,}"),
        "",
    ]

    columns = schema.get("columns", [])
    mismatches = schema.get("mismatch_columns", [])

    if columns:
        lines.append("  Column type inference:")
        for col in columns:
            name = col.get("name", "?")
            ctype = col.get("inferred_type", "?")
            null_pct = col.get("null_pct", 0) or 0
            unique = col.get("unique_count", 0)
            all_miss = col.get("all_missing", False)
            mismatch = col.get("mismatch_warning", False)
            flags = []
            if all_miss:
                flags.append("ALL MISSING")
            if mismatch:
                flags.append("TYPE MISMATCH")
            flag_str = f"  [{', '.join(flags)}]" if flags else ""
            lines.append(
                f"    {name:<28} {ctype:<12}  null: {null_pct}%  unique: {unique}{flag_str}"
            )
        lines.append("")

    if mismatches:
        lines.append("  Type-mismatch warnings:")
        for col in mismatches:
            lines.append(_bullet(
                f"{col}  — stored as string but majority of values are numeric"
            ))
        lines.append("")
    else:
        lines.append("  Type-mismatch warnings: None")
        lines.append("")

    return lines


def _section_missingness(missingness: dict) -> list:
    lines = _section_header(3, "MISSINGNESS SUMMARY")

    if not missingness.get("applicable", True):
        return lines + _na_block(missingness.get("reason", "Missingness check not applicable"))

    total_missing = missingness.get("total_missing", 0)
    missing_pct   = missingness.get("missing_pct_overall", 0.0) or 0.0
    rows_miss     = missingness.get("rows_with_missing", 0)
    rows_miss_pct = missingness.get("rows_with_missing_pct", 0.0) or 0.0
    total_cells   = missingness.get("total_cells", 0)
    per_col       = missingness.get("per_column", [])

    lines += [
        _kv("Total Missing Cells",  f"{total_missing:,} of {total_cells:,}"),
        _kv("Overall Missing %",    f"{missing_pct}%"),
        _kv("Rows with Missing",    f"{rows_miss:,} ({rows_miss_pct}% of rows)"),
        "",
    ]

    if per_col:
        lines.append("  Per-column breakdown (columns with missing values only):")
        for col in per_col:
            action = col.get("suggested_action", "")
            lines.append(
                _bullet(f"{col['column']}: {col['null_count']:,} missing ({col['null_pct']}%)  — {action}")
            )
        lines.append("")
    else:
        lines.append("  No columns with missing values.")
        lines.append("")

    return lines


def _section_duplicates(duplicates: dict) -> list:
    lines = _section_header(4, "DUPLICATE ANALYSIS")

    if not duplicates.get("applicable", True):
        return lines + _na_block(duplicates.get("reason", "Duplicate check not applicable"))

    dup_count = duplicates.get("duplicate_row_count", 0)
    dup_pct   = duplicates.get("duplicate_pct", 0.0) or 0.0
    risk      = duplicates.get("risk_label", "N/A")

    lines += [
        _kv("Duplicate Row Count", f"{dup_count:,}"),
        _kv("Duplicate %",         f"{dup_pct}%"),
        _kv("Risk Label",          risk),
        "",
    ]

    if dup_count == 0:
        lines.append("  No exact duplicate rows detected.")
    else:
        lines.append(
            _bullet(
                f"{dup_count:,} exact duplicate row(s) found "
                f"({dup_pct}% of total rows)."
            )
        )
    lines.append("")
    return lines


def _section_outliers(outliers: dict) -> list:
    lines = _section_header(5, "NUMERIC OUTLIER SUMMARY")

    if not outliers.get("applicable", True):
        return lines + _na_block(outliers.get("reason", "Outlier check not applicable"))

    lines.append("  Method: IQR (Interquartile Range)")
    lines.append("          Lower bound = Q1 − 1.5 × IQR")
    lines.append("          Upper bound = Q3 + 1.5 × IQR")
    lines.append("")

    numeric_cols = outliers.get("numeric_columns", [])
    applicable_cols = [c for c in numeric_cols if c.get("applicable", True)]
    na_cols         = [c for c in numeric_cols if not c.get("applicable", True)]

    if not applicable_cols and not na_cols:
        lines.append("  No numeric columns available for outlier analysis.")
        lines.append("")
        return lines

    if applicable_cols:
        # Header row
        hdr = f"  {'Column':<22} {'Q1':>10} {'Q3':>10} {'Lower':>10} {'Upper':>10} {'Outliers':>10} {'%':>7}"
        lines.append(hdr)
        lines.append("  " + "-" * (len(hdr) - 2))
        for col in applicable_cols:
            cname = col.get("column", "?")[:21]
            q1    = col.get("q1", "N/A")
            q3    = col.get("q3", "N/A")
            lb    = col.get("lower_bound", "N/A")
            ub    = col.get("upper_bound", "N/A")
            oc    = col.get("outlier_count", 0)
            op    = col.get("outlier_pct", 0.0) or 0.0
            lines.append(
                f"  {cname:<22} {str(q1):>10} {str(q3):>10} "
                f"{str(lb):>10} {str(ub):>10} {str(oc):>10} {str(op)+'%':>7}"
            )
        lines.append("")

    if na_cols:
        lines.append("  Columns skipped (insufficient data):")
        for col in na_cols:
            lines.append(_bullet(f"{col.get('column', '?')}: {col.get('reason', 'N/A')}"))
        lines.append("")

    return lines


def _section_imbalance(imbalance: dict) -> list:
    lines = _section_header(6, "CLASS IMBALANCE SUMMARY")

    if not imbalance.get("applicable", True):
        return lines + _na_block(imbalance.get("reason", "Class imbalance check not applicable"))

    target  = imbalance.get("target_col", "N/A")
    label   = imbalance.get("imbalance_label", "N/A")
    ratio   = imbalance.get("majority_to_minority_ratio")
    dist    = imbalance.get("class_distribution", [])

    ratio_str = f"{ratio}x" if ratio is not None else "N/A"

    lines += [
        _kv("Target Column",          target),
        _kv("Imbalance Label",        label),
        _kv("Majority / Minority Ratio", ratio_str),
        "",
    ]

    if dist:
        lines.append("  Class distribution:")
        majority_cls = dist[0]["class"] if dist else None
        minority_cls = dist[-1]["class"] if len(dist) > 1 else None
        for cls in dist:
            role = ""
            if cls["class"] == majority_cls and len(dist) > 1:
                role = "  (majority)"
            elif cls["class"] == minority_cls and len(dist) > 1:
                role = "  (minority)"
            lines.append(
                f"    {cls['class']:<20} {cls['count']:>8,}  ({cls['pct']}%){role}"
            )
        lines.append("")

    return lines


def _section_leakage(leakage: dict) -> list:
    lines = _section_header(7, "LEAKAGE-RISK INDICATORS")

    if not leakage.get("applicable", True):
        return lines + _na_block(leakage.get("reason", "Leakage check not applicable"))

    flagged   = leakage.get("flagged_columns", [])
    flag_count = leakage.get("flag_count", 0)
    keywords  = leakage.get("keywords_checked", [])

    lines += [
        _kv("Flagged Columns", flag_count),
        "",
    ]

    if flagged:
        lines.append("  Flagged columns:")
        for col in flagged:
            kws = ", ".join(col.get("matched_keywords", []))
            lines.append(_bullet(f"{col['column']}  [matched keyword(s): {kws}]"))
        lines.append("")
    else:
        lines.append("  No leakage-risk columns detected.")
        lines.append("")

    if keywords:
        kw_line = ", ".join(sorted(keywords))
        lines.append("  Keywords checked:")
        for chunk in textwrap.wrap(kw_line, width=_REPORT_WIDTH - 4,
                                   initial_indent="    ",
                                   subsequent_indent="    "):
            lines.append(chunk)
        lines.append("")

    return lines


def _section_readiness(readiness: dict) -> list:
    lines = _section_header(8, "MODELING READINESS SCORE")

    score     = readiness.get("score", "N/A")
    band      = readiness.get("score_band", readiness.get("category", "N/A"))
    penalties = readiness.get("penalties", [])
    na_checks = readiness.get("not_applicable", [])
    expl      = readiness.get("explanation", "")

    lines += [
        _kv("Score",      f"{score} / 100"),
        _kv("Score Band", band),
        "",
    ]

    if expl:
        lines.append("  Summary:")
        lines.append(_wrap_paragraph(expl, indent=4))
        lines.append("")

    # Score band reference
    lines += [
        "  Score band reference:",
        "    >= 85   Ready",
        "    70-84   Acceptable with preprocessing",
        "    50-69   Needs preprocessing",
        "    < 50    High risk",
        "",
    ]

    # Applied penalties
    total_deducted = sum(p.get("penalty", 0) for p in penalties)
    if penalties:
        lines.append(f"  Applied penalties (total deducted: -{total_deducted}):")
        for p in penalties:
            check = p.get("check", p.get("factor", "?"))
            pen   = p.get("penalty", 0)
            rule  = p.get("rule", p.get("detail", ""))
            lines.append(_bullet(f"-{pen:>3}  {check}: {rule}"))
        lines.append("")
    else:
        lines.append("  Applied penalties: None")
        lines.append("")

    # Not-applicable checks
    if na_checks:
        lines.append("  Not-applicable checks:")
        for na in na_checks:
            check  = na.get("check", "?")
            reason = na.get("reason", "")
            lines.append(_bullet(f"{check}: {reason}"))
        lines.append("")

    return lines


def _section_recommendations(
    schema: dict,
    missingness: dict,
    duplicates: dict,
    outliers: dict,
    imbalance: dict,
    leakage: dict,
) -> list:
    """
    Generate recommendations only from confirmed audit findings.
    Each recommendation maps to exactly one audit check.
    """
    lines = _section_header(9, "RECOMMENDATIONS")

    recs:  list = []   # (heading, detail)
    clean: list = []   # checks with no action needed
    na:    list = []   # not-applicable checks

    # ── Missingness ──────────────────────────────────────────────
    if not missingness.get("applicable", True):
        na.append("Missingness")
    else:
        pct = missingness.get("missing_pct_overall", 0.0) or 0.0
        if pct > 1.0:
            per_col = missingness.get("per_column", [])
            affected = [c["column"] for c in per_col]
            detail = (
                f"Overall missingness is {pct}%. "
                "Consider imputing missing values using column statistics "
                "(mean, median, or mode) or filtering rows where critical "
                "columns are missing."
            )
            if affected:
                detail += f" Affected columns: {', '.join(affected)}."
            recs.append(("High missingness detected", detail))
        else:
            clean.append("Missingness")

    # ── Duplicates ───────────────────────────────────────────────
    if not duplicates.get("applicable", True):
        na.append("Duplicates")
    else:
        dup_count = duplicates.get("duplicate_row_count", 0)
        dup_pct   = duplicates.get("duplicate_pct", 0.0) or 0.0
        if dup_count > 0:
            recs.append((
                "Duplicate rows detected",
                f"{dup_count:,} exact duplicate row(s) found ({dup_pct}%). "
                "Deduplicate the dataset before training to prevent "
                "data leakage between train and test splits and inflated "
                "evaluation metrics.",
            ))
        else:
            clean.append("Duplicates")

    # ── Datatype anomalies ───────────────────────────────────────
    if not schema.get("applicable", True):
        na.append("Datatype anomalies")
    else:
        mismatches = schema.get("mismatch_columns", [])
        if mismatches:
            recs.append((
                "Datatype anomalies detected",
                f"Column(s) {', '.join(mismatches)} appear to store numeric "
                "values as strings. Correct the column types before "
                "feature engineering or numeric transformations.",
            ))
        else:
            clean.append("Datatype anomalies")

    # ── Outliers ─────────────────────────────────────────────────
    if not outliers.get("applicable", True):
        na.append("Outliers")
    else:
        applicable_cols = [
            c for c in outliers.get("numeric_columns", [])
            if c.get("applicable", True) and (c.get("outlier_pct") or 0) > 10
        ]
        if applicable_cols:
            col_names = [c["column"] for c in applicable_cols]
            max_pct = max(c.get("outlier_pct", 0) or 0 for c in applicable_cols)
            recs.append((
                "Outliers detected in numeric columns",
                f"{len(col_names)} column(s) exceed 10% IQR outlier rate "
                f"(highest: {max_pct}%): {', '.join(col_names)}. "
                "Investigate these values before modelling. "
                "Do not apply automatic outlier removal without domain review.",
            ))
        else:
            clean.append("Outliers")

    # ── Class imbalance ──────────────────────────────────────────
    if not imbalance.get("applicable", True):
        na.append("Class imbalance")
    else:
        label  = imbalance.get("imbalance_label", "")
        target = imbalance.get("target_col", "target column")
        ratio  = imbalance.get("majority_to_minority_ratio")
        if label == "Severe imbalance":
            ratio_str = f" ({ratio}x ratio)" if ratio else ""
            recs.append((
                "Severe class imbalance detected",
                f"'{target}' shows severe imbalance{ratio_str}. "
                "Consider resampling techniques (e.g. oversampling the "
                "minority class or undersampling the majority class) or "
                "use class-weighted loss functions during model training.",
            ))
        elif label == "Moderate imbalance":
            recs.append((
                "Moderate class imbalance detected",
                f"'{target}' shows moderate imbalance. "
                "Monitor class-specific metrics (precision, recall, F1) "
                "during evaluation. Resampling may or may not be needed "
                "depending on the modelling objective.",
            ))
        else:
            clean.append("Class imbalance")

    # ── Leakage risk ─────────────────────────────────────────────
    if not leakage.get("applicable", True):
        na.append("Leakage risk")
    else:
        flag_count = leakage.get("flag_count", 0)
        if flag_count > 0:
            flagged_names = [
                f["column"] for f in leakage.get("flagged_columns", [])
            ]
            recs.append((
                "Leakage-risk columns detected",
                f"{flag_count} column(s) contain leakage-risk keywords: "
                f"{', '.join(flagged_names)}. "
                "Review each flagged column carefully and exclude any that "
                "encode information derived from or correlated with the "
                "target variable before modelling.",
            ))
        else:
            clean.append("Leakage risk")

    # ── Format output ────────────────────────────────────────────
    if not recs:
        lines.append("  No action required.")
        lines.append("")
        lines.append("  All evaluated checks passed without actionable findings.")
        lines.append("")
    else:
        for heading, detail in recs:
            lines.append(f"  [!] {heading}")
            lines.append(_wrap_paragraph(detail, indent=6))
            lines.append("")

    if clean:
        lines.append("  No action required for:")
        lines.append(_bullet(", ".join(clean)))
        lines.append("")

    if na:
        lines.append("  Not applicable (not evaluated):")
        lines.append(_bullet(", ".join(na)))
        lines.append("")

    return lines


# ─────────────────────────────────────────────────────────────────
# Phase 6 — Main report generator
# ─────────────────────────────────────────────────────────────────

def generate_text_report(
    meta: dict,
    schema: dict,
    missingness: dict,
    duplicates: dict,
    outliers: dict,
    imbalance: dict,
    leakage: dict,
    readiness: dict,
) -> str:
    """
    Generate a structured plain-text audit report from audit engine output.

    Sections (in order):
      1. Dataset Overview
      2. Schema Diagnostics
      3. Missingness Summary
      4. Duplicate Analysis
      5. Numeric Outlier Summary
      6. Class Imbalance Summary
      7. Leakage-Risk Indicators
      8. Modeling Readiness Score
      9. Recommendations

    Each section that is not applicable is explicitly labeled.
    Recommendations are generated only from confirmed audit findings.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    target = imbalance.get("target_col") or "Not selected"

    lines: list = []

    # ── Report header ──────────────────────────────────────────────
    lines += [
        _MAJOR_SEP,
        "  AUTOMATED DATASET RELIABILITY AND MODELING READINESS REPORT",
        _MAJOR_SEP,
        _kv("Report generated",  now),
        _kv("File",              meta.get("filename", "N/A")),
        _kv("Rows",              f"{meta.get('rows', 0):,}"),
        _kv("Columns",           meta.get("cols", 0)),
        _kv("Target Column",     target),
        "",
    ]

    # ── Sections ───────────────────────────────────────────────────
    lines += _section_overview(meta, imbalance)
    lines += _section_schema(schema)
    lines += _section_missingness(missingness)
    lines += _section_duplicates(duplicates)
    lines += _section_outliers(outliers)
    lines += _section_imbalance(imbalance)
    lines += _section_leakage(leakage)
    lines += _section_readiness(readiness)
    lines += _section_recommendations(
        schema, missingness, duplicates, outliers, imbalance, leakage
    )

    # ── Report footer ──────────────────────────────────────────────
    lines += [_MAJOR_SEP, "  END OF REPORT", _MAJOR_SEP]

    return "\n".join(lines)




# ────────────────────────────────────────────────
# API routes
# ────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ─── /api/parse ──────────────────────────────────
@app.post("/api/parse")
async def parse_csv_endpoint(file: UploadFile = File(...)):
    """
    Phase 3 parsing endpoint.
    Validates and parses the uploaded CSV file.
    Returns: meta, preview, column_info, warnings.
    Does NOT run audit computations.
    """
    filename = file.filename or ""

    # 1. Validate extension
    try:
        validate_file_extension(filename)
    except ParseError as exc:
        return _parse_error_response(exc.code, exc.message, exc.hint, status_code=400)

    # 2. Read bytes
    try:
        raw_bytes = await file.read()
    except Exception as exc:
        return _parse_error_response(
            "read_error",
            f"Failed to read the uploaded file: {exc}",
            "Try uploading the file again.",
            status_code=400,
        )

    # 3. File size check
    if len(raw_bytes) == 0:
        return _parse_error_response(
            "empty_file",
            "The uploaded file is empty (0 bytes).",
            "Ensure the CSV contains at least a header row and one data row.",
            status_code=422,
        )
    if len(raw_bytes) > MAX_FILE_BYTES:
        size_mb = len(raw_bytes) / (1024 * 1024)
        return _parse_error_response(
            "too_large",
            f"File size ({size_mb:.1f} MB) exceeds the maximum allowed ({MAX_FILE_MB} MB).",
            "Reduce the file size or split it into smaller parts before uploading.",
            status_code=413,
        )

    # 4. Validate MIME type (soft check — browser-supplied, unreliable)
    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # Only hard-reject clearly non-text MIME types
        clearly_binary = (
            content_type.startswith("image/")
            or content_type.startswith("video/")
            or content_type.startswith("audio/")
            or content_type in (
                "application/zip", "application/pdf",
                "application/x-zip-compressed",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
                "application/vnd.ms-excel.sheet.macroEnabled.12",  # .xlsm
            )
        )
        if clearly_binary:
            return _parse_error_response(
                "unsupported_file_type",
                f"File type '{content_type}' is not supported.",
                "Only CSV files are accepted. Excel (.xlsx, .xls) and other formats are not supported.",
                status_code=400,
            )

    # 5. Parse
    try:
        result = parse_csv_bytes(raw_bytes, filename)
    except ParseError as exc:
        return _parse_error_response(exc.code, exc.message, exc.hint, status_code=422)
    except Exception as exc:
        return _parse_error_response(
            "unexpected_error",
            f"An unexpected error occurred: {str(exc)[:300]}",
            "Verify the file is a well-formed CSV and try again.",
            status_code=500,
        )

    # 6. Return parse result (strip internal df)
    return sanitize_for_json({
        "parse_status": "success",
        "meta": result["meta"],
        "preview": result["preview"],
        "column_info": result["column_info"],
        "warnings": result["warnings"],
    })


# ─── /api/audit ──────────────────────────────────
@app.post("/api/audit")
async def audit_csv(
    file: UploadFile = File(...),
    target_col: Optional[str] = Form(default=None),
):
    """
    Full audit endpoint (Phase 4).

    Flow:
      1. Validate + parse CSV via parse_csv_bytes() → raw string df
      2. Run all six audit modules via audit_engine.run_audit() on raw strings
      3. Compute readiness score from audit findings
      4. Return structured result

    The audit engine works on dtype=str DataFrames and applies its own
    type-inference heuristics — no pre-coercion here.
    """
    filename = file.filename or ""

    # Validate extension
    try:
        validate_file_extension(filename)
    except ParseError as exc:
        raise HTTPException(status_code=400, detail=exc.message)

    # Read bytes
    raw_bytes = await file.read()

    # Size check
    if len(raw_bytes) == 0:
        raise HTTPException(status_code=422, detail="The uploaded file is empty.")
    if len(raw_bytes) > MAX_FILE_BYTES:
        size_mb = len(raw_bytes) / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File size ({size_mb:.1f} MB) exceeds the {MAX_FILE_MB} MB limit.",
        )

    # Parse using robust Phase-3 parser (returns df with dtype=str)
    try:
        parse_result = parse_csv_bytes(raw_bytes, filename)
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=exc.message)

    df_raw: pd.DataFrame = parse_result["df"]  # raw strings, dtype=str

    # Dataset metadata
    meta = {
        "filename": filename,
        "rows": len(df_raw),
        "cols": df_raw.shape[1],
        "column_names": df_raw.columns.tolist(),
        "encoding": parse_result["meta"].get("encoding", "utf-8"),
        "delimiter": parse_result["meta"].get("delimiter", ","),
    }

    # Preview — raw string values for faithful display
    preview_df = df_raw.head(MAX_PREVIEW_ROWS)
    preview_data = preview_df.where(pd.notnull(preview_df), None).to_dict(orient="records")

    # ── Run audit engine on raw-string DataFrame ──────────────────
    # run_audit handles type-inference, IQR coercion, and all edge cases internally.
    findings = run_audit(df_raw, target_col=target_col or None)

    # ── Compute readiness score from findings ─────────────────────
    readiness = compute_readiness_score(
        schema=findings["schema"],
        missingness=findings["missingness"],
        duplicates=findings["duplicates"],
        outliers=findings["outliers"],
        imbalance=findings["imbalance"],
        leakage=findings["leakage"],
    )

    result = {
        "meta": meta,
        "preview": preview_data,
        "parse_warnings": parse_result["warnings"],
        # Audit findings (grouped by module)
        "schema": findings["schema"],
        "missingness": findings["missingness"],
        "duplicates": findings["duplicates"],
        "outliers": findings["outliers"],
        "imbalance": findings["imbalance"],
        "leakage": findings["leakage"],
        # Computed score
        "readiness": readiness,
    }
    return engine_sanitize(result)


@app.post("/api/report", response_class=PlainTextResponse)
async def download_report(payload: dict):
    """Generate and return a text report from the audit payload."""
    try:
        report = generate_text_report(
            meta=payload.get("meta", {}),
            schema=payload.get("schema", {}),
            missingness=payload.get("missingness", {}),
            duplicates=payload.get("duplicates", {}),
            outliers=payload.get("outliers", {}),
            imbalance=payload.get("imbalance", {}),
            leakage=payload.get("leakage", {}),
            readiness=payload.get("readiness", {}),
        )
        return PlainTextResponse(
            content=report,
            media_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="audit_report.txt"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")



"""
audit_engine.py
Deterministic, rule-based audit checks for the
Automated Dataset Reliability and Modeling Readiness Inspector.

All checks operate on raw string values (dtype=str).
No coercion, no ML models, no external APIs, no fuzzy matching.
"""

import math
import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────

# Phase 4 expanded leakage keyword set
LEAKAGE_KEYWORDS: frozenset = frozenset({
    "id", "target", "label", "outcome", "status", "result",
    "final", "prediction", "future", "post", "completed", "discharge",
})

# Type-inference thresholds
NUMERIC_THRESHOLD = 0.80        # ≥80% of non-null values parseable as float → numeric
DATETIME_THRESHOLD = 0.80       # ≥80% of non-null values match date patterns → datetime
MAX_CATEGORICAL_UNIQUE = 20     # ≤20 unique values → categorical regardless of ratio
MISMATCH_THRESHOLD = 0.50       # >50% numeric in a text column → mismatch warning

# Outlier minimum sample size (IQR is unreliable below 4 values)
MIN_IQR_SAMPLE = 4

# Imbalance
MAX_IMBALANCE_CLASSES = 20      # beyond this, imbalance is "not applicable"

# Datetime regex patterns (ordered from most to least specific)
_DATETIME_PATTERNS: List[re.Pattern] = [
    re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$"),  # ISO 8601
    re.compile(r"^\d{4}/\d{2}/\d{2}$"),                              # YYYY/MM/DD
    re.compile(r"^\d{2}[/-]\d{2}[/-]\d{4}$"),                        # DD/MM/YYYY or MM/DD/YYYY
    re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"),           # ISO datetime with seconds
]


# ─────────────────────────────────────────────────────────────────
# JSON-safety helpers
# ─────────────────────────────────────────────────────────────────

def _safe_round(val, ndigits: int = 4) -> Optional[float]:
    """Return float rounded to ndigits, or None if NaN/Inf/None."""
    if val is None:
        return None
    try:
        v = float(val)
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, ndigits)
    except (TypeError, ValueError):
        return None


def sanitize(obj):
    """Recursively convert numpy scalars, NaN, and Inf to JSON-safe values."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, np.floating):
        v = float(obj)
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 4)
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


# ─────────────────────────────────────────────────────────────────
# Type inference (heuristics only — no coercion)
# ─────────────────────────────────────────────────────────────────

def _is_numeric_str(val: str) -> bool:
    """Return True if val (already a string) can be parsed as a float."""
    v = val.strip().replace(",", "").replace(" ", "")
    if not v:
        return False
    try:
        float(v)
        return True
    except ValueError:
        return False


def _is_datetime_str(val: str) -> bool:
    """Return True if val looks like a date or datetime string."""
    v = val.strip()
    return any(p.match(v) for p in _DATETIME_PATTERNS)


def infer_column_type(series: pd.Series) -> str:
    """
    Heuristic type inference on raw string values.
    Order: numeric → datetime → categorical → text → empty.
    Does NOT coerce or modify values.

    Returns one of: 'numeric' | 'datetime' | 'categorical' | 'text' | 'empty'
    """
    non_null = series.dropna()
    n = len(non_null)
    if n == 0:
        return "empty"

    # 1. Numeric
    numeric_hits = sum(1 for v in non_null if _is_numeric_str(str(v)))
    if numeric_hits / n >= NUMERIC_THRESHOLD:
        return "numeric"

    # 2. Datetime-like
    dt_hits = sum(1 for v in non_null if _is_datetime_str(str(v)))
    if dt_hits / n >= DATETIME_THRESHOLD:
        return "datetime"

    # 3. Categorical (low cardinality — regardless of ratio)
    unique_count = non_null.nunique()
    if unique_count <= MAX_CATEGORICAL_UNIQUE:
        return "categorical"

    # 4. Default: free text / high-cardinality string
    return "text"


def _has_mismatch_warning(series: pd.Series, inferred_type: str) -> bool:
    """
    Flag a column as having a type-mismatch warning when:
    - its inferred type is 'text'
    - AND >50% of its non-null values are parseable as numbers

    This catches columns stored as strings that should be numeric.
    """
    if inferred_type != "text":
        return False
    non_null = series.dropna()
    if len(non_null) == 0:
        return False
    numeric_hits = sum(1 for v in non_null if _is_numeric_str(str(v)))
    return (numeric_hits / len(non_null)) > MISMATCH_THRESHOLD


# ─────────────────────────────────────────────────────────────────
# Module 1 — Schema diagnostics
# ─────────────────────────────────────────────────────────────────

def _audit_schema(df: pd.DataFrame, col_types: Dict[str, str]) -> Dict:
    """
    Per-column schema summary:
    - inferred type, unique count, null count/%, all-missing flag, mismatch warning.
    """
    n_rows = len(df)
    columns = []
    mismatch_columns: List[str] = []

    for col in df.columns:
        series = df[col]
        inferred = col_types[col]
        null_count = int(series.isna().sum())
        unique_count = int(series.dropna().nunique())
        all_missing = null_count == n_rows
        mismatch = _has_mismatch_warning(series, inferred)

        if mismatch:
            mismatch_columns.append(col)

        columns.append({
            "name": col,
            "inferred_type": inferred,
            "unique_count": unique_count,
            "null_count": null_count,
            "null_pct": _safe_round(null_count / n_rows * 100) if n_rows else 0.0,
            "all_missing": all_missing,
            "mismatch_warning": mismatch,
        })

    return {
        "applicable": True,
        "row_count": n_rows,
        "column_count": int(df.shape[1]),
        "columns": columns,
        "mismatch_columns": mismatch_columns,
    }


# ─────────────────────────────────────────────────────────────────
# Module 2 — Missingness
# ─────────────────────────────────────────────────────────────────

def _audit_missingness(df: pd.DataFrame) -> Dict:
    """
    Missingness summary:
    - total missing cells
    - overall missing %
    - rows containing at least one missing value
    - per-column breakdown (sorted descending by missing count)
    """
    n_rows = len(df)
    total_cells = int(df.size)
    total_missing = int(df.isna().sum().sum())
    rows_with_missing = int(df.isna().any(axis=1).sum())

    per_column = []
    for col in df.columns:
        nc = int(df[col].isna().sum())
        if nc > 0:
            per_column.append({
                "column": col,
                "null_count": nc,
                "null_pct": _safe_round(nc / n_rows * 100) if n_rows else 0.0,
                "suggested_action": (
                    "Consider dropping — high missingness (>50%)"
                    if nc / max(n_rows, 1) > 0.50
                    else "Impute or flag as missing"
                ),
            })

    per_column.sort(key=lambda x: x["null_count"], reverse=True)

    return {
        "applicable": True,
        "total_cells": total_cells,
        "total_missing": total_missing,
        "missing_pct_overall": _safe_round(total_missing / total_cells * 100) if total_cells else 0.0,
        "rows_with_missing": rows_with_missing,
        "rows_with_missing_pct": _safe_round(rows_with_missing / n_rows * 100) if n_rows else 0.0,
        "per_column": per_column,
    }


# ─────────────────────────────────────────────────────────────────
# Module 3 — Duplicate detection
# ─────────────────────────────────────────────────────────────────

def _audit_duplicates(df: pd.DataFrame) -> Dict:
    """Exact duplicate row count and percentage, with risk label."""
    if df.shape[1] <= 1:
        return {
            "applicable": False,
            "reason": "Single-column dataset — exact duplicate detection requires multiple columns",
        }

    dup_count = int(df.duplicated().sum())
    n_rows = len(df)
    dup_pct = _safe_round(dup_count / n_rows * 100) if n_rows else 0.0

    # Risk label thresholds
    if (dup_pct or 0) < 1.0:
        risk_label = "Low"
    elif (dup_pct or 0) < 10.0:
        risk_label = "Moderate"
    else:
        risk_label = "High"

    return {
        "applicable": True,
        "duplicate_row_count": dup_count,
        "duplicate_pct": dup_pct,
        "risk_label": risk_label,
    }


# ─────────────────────────────────────────────────────────────────
# Module 4 — Numeric outlier detection (IQR)
# ─────────────────────────────────────────────────────────────────

def _coerce_to_numeric(series: pd.Series) -> pd.Series:
    """
    Coerce raw-string series to float for outlier computation.
    Non-parseable values become NaN.  This coercion is limited to
    the outlier module only — raw values are never modified.
    """
    return pd.to_numeric(
        series.apply(lambda v: str(v).strip().replace(",", "") if pd.notna(v) else v),
        errors="coerce",
    )


def _audit_outliers(df: pd.DataFrame, col_types: Dict[str, str]) -> Dict:
    """
    IQR-based outlier detection for each inferred-numeric column.

    For each numeric column:
        Q1, Q3, IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outlier_count = values outside [lower, upper]
    """
    numeric_cols = [col for col, t in col_types.items() if t == "numeric"]

    if not numeric_cols:
        return {
            "applicable": False,
            "reason": "No numeric columns detected in this dataset",
            "numeric_columns": [],
        }

    results = []
    for col in numeric_cols:
        num_series = _coerce_to_numeric(df[col]).dropna()

        if len(num_series) < MIN_IQR_SAMPLE:
            results.append({
                "column": col,
                "applicable": False,
                "reason": f"Insufficient non-null values ({len(num_series)}) — IQR requires at least {MIN_IQR_SAMPLE}",
            })
            continue

        q1 = _safe_round(float(num_series.quantile(0.25)))
        q3 = _safe_round(float(num_series.quantile(0.75)))

        if q1 is None or q3 is None:
            results.append({"column": col, "applicable": False, "reason": "Could not compute quartiles"})
            continue

        iqr = round(q3 - q1, 4)
        lower = round(q1 - 1.5 * iqr, 4)
        upper = round(q3 + 1.5 * iqr, 4)

        outlier_mask = (num_series < lower) | (num_series > upper)
        outlier_count = int(outlier_mask.sum())
        n_valid = len(num_series)

        results.append({
            "column": col,
            "applicable": True,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_bound": lower,
            "upper_bound": upper,
            "outlier_count": outlier_count,
            "outlier_pct": _safe_round(outlier_count / n_valid * 100),
        })

    return {"applicable": True, "numeric_columns": results}


# ─────────────────────────────────────────────────────────────────
# Module 5 — Class imbalance
# ─────────────────────────────────────────────────────────────────

def _audit_imbalance(df: pd.DataFrame, target_col: Optional[str]) -> Dict:
    """
    Class distribution for the selected target column.
    Computes majority-to-minority ratio and assigns an imbalance label.

    Labels:
        Balanced              ratio < 1.5
        Moderate imbalance    1.5 ≤ ratio < 5.0
        Severe imbalance      ratio ≥ 5.0  (or single class)
    """
    if not target_col:
        return {
            "applicable": False,
            "not_selected": True,
            "too_many_classes": False,
            "reason": "No target column selected",
            "target_col": None,
        }

    if target_col not in df.columns:
        return {
            "applicable": False,
            "not_selected": True,
            "too_many_classes": False,
            "reason": f"Target column '{target_col}' was not found in the dataset",
            "target_col": target_col,
        }

    series = df[target_col].dropna()

    if len(series) == 0:
        return {
            "applicable": False,
            "not_selected": False,
            "too_many_classes": False,
            "reason": "Target column is entirely missing — no values to analyse",
            "target_col": target_col,
        }

    value_counts = series.value_counts()
    n_classes = len(value_counts)

    if n_classes > MAX_IMBALANCE_CLASSES:
        return {
            "applicable": False,
            "not_selected": False,
            "too_many_classes": True,
            "reason": (
                f"Target column has {n_classes} unique values. "
                f"Class imbalance analysis applies to columns with ≤{MAX_IMBALANCE_CLASSES} distinct classes."
            ),
            "target_col": target_col,
        }

    total = len(series)
    distribution = [
        {
            "class": str(cls),
            "count": int(cnt),
            "pct": _safe_round(cnt / total * 100),
        }
        for cls, cnt in value_counts.items()
    ]

    if n_classes == 1:
        ratio = None
        imbalance_label = "Severe imbalance"
    else:
        majority_count = distribution[0]["count"]
        minority_count = distribution[-1]["count"]
        ratio = _safe_round(majority_count / minority_count) if minority_count > 0 else None

        if ratio is None:
            imbalance_label = "Severe imbalance"
        elif ratio < 1.5:
            imbalance_label = "Balanced"
        elif ratio < 5.0:
            imbalance_label = "Moderate imbalance"
        else:
            imbalance_label = "Severe imbalance"

    return {
        "applicable": True,
        "not_selected": False,
        "too_many_classes": False,
        "target_col": target_col,
        "class_distribution": distribution,
        "majority_to_minority_ratio": ratio,
        "imbalance_label": imbalance_label,
    }


# ─────────────────────────────────────────────────────────────────
# Module 6 — Leakage-risk heuristics
# ─────────────────────────────────────────────────────────────────

def _audit_leakage(df: pd.DataFrame) -> Dict:
    """
    Flag column names that contain any leakage-risk keyword (case-insensitive substring match).
    Keywords: id, target, label, outcome, status, result, final, prediction,
              future, post, completed, discharge.
    """
    flagged = []
    for col in df.columns:
        col_lower = col.lower()
        matched = sorted(kw for kw in LEAKAGE_KEYWORDS if kw in col_lower)
        if matched:
            flagged.append({"column": col, "matched_keywords": matched})

    return {
        "applicable": True,
        "flagged_columns": flagged,
        "flag_count": len(flagged),
        "keywords_checked": sorted(LEAKAGE_KEYWORDS),
    }


# ─────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────

def run_audit(df: pd.DataFrame, target_col: Optional[str] = None) -> Dict:
    """
    Run all six audit checks on the given DataFrame.

    The DataFrame should contain raw string values (dtype=str from parse stage).
    Type inference is applied internally; values are never coerced in-place.

    Parameters
    ----------
    df          : pandas DataFrame with raw string values
    target_col  : optional name of the column to use for class imbalance analysis

    Returns
    -------
    dict with keys: schema, missingness, duplicates, outliers, imbalance, leakage
    Each value is a module-result dict that always contains `applicable: bool`.
    """
    # Edge case: empty dataset
    if df.empty or df.shape[0] == 0 or df.shape[1] == 0:
        not_applicable = {"applicable": False, "reason": "Empty dataset — no rows or columns to inspect"}
        return sanitize({
            "schema": not_applicable,
            "missingness": not_applicable,
            "duplicates": not_applicable,
            "outliers": not_applicable,
            "imbalance": {**not_applicable, "not_selected": False, "too_many_classes": False},
            "leakage": not_applicable,
        })

    # Infer column types from raw string values (no coercion)
    col_types = {col: infer_column_type(df[col]) for col in df.columns}

    findings = {
        "schema":      _audit_schema(df, col_types),
        "missingness": _audit_missingness(df),
        "duplicates":  _audit_duplicates(df),
        "outliers":    _audit_outliers(df, col_types),
        "imbalance":   _audit_imbalance(df, target_col),
        "leakage":     _audit_leakage(df),
    }

    return sanitize(findings)

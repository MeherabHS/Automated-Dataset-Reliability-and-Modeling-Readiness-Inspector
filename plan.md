# plan.md — Automated Dataset Reliability and Modeling Readiness Inspector (Updated)

## 1. Objectives
- Build a **single-page** web app called **“Automated Dataset Reliability and Modeling Readiness Inspector”**.
- Provide a **minimal, clean interface** for:
  - uploading a **CSV-only** dataset,
  - parsing it **safely** (encoding/delimiter/malformed row handling),
  - previewing the first rows,
  - running a deterministic **rule-based audit engine** across core dataset-quality checks,
  - converting audit findings into a transparent **modeling readiness score (0–100)**,
  - and downloading a structured text report.
- Maintain a **modular backend (FastAPI)** and progress through phases:
  - UI scaffold → data ingestion → audit engine → **scoring** → reporting → polish.
- Enforce constraints: **CSV-only**, **no authentication**, **no database**, **no cloud persistence**, **no Excel/PDF support**, **no model training**, **no settings pages**, **no multi-dataset sessions**, **no automatic preprocessing**.

**Current status**
- ✅ **Phase 1 (backend MVP capability)** complete.
- ✅ **Phase 2 (UI scaffold)** complete with **100% frontend pass rate (26/26)**.
- ✅ **Phase 3 (data ingestion)** complete:
  - Added **`POST /api/parse`** with robust validation + parsing + structured errors.
  - Updated frontend to a **two-step flow**: **Upload & Preview** → **Run Full Audit**.
- ✅ **Phase 4 (audit engine)** complete:
  - Implemented **all 6 audit modules** in `backend/audit_engine.py` using deterministic heuristics on **raw strings**.
  - All modules return `applicable: bool` with clear `reason` when not applicable.
  - Frontend updated to render the new audit structure and includes a **target column selector** that re-runs the audit with `target_col`.
  - Backend tests: **100% pass rate** for Phase 4 expectations.
- ✅ **Phase 5 (scoring)** complete (**100% test pass rate**):
  - Implemented exact spec penalty rules, 4 score bands, `not_applicable` list, and an explanation generator.
  - Frontend readiness panel updated to display: band badge, explanation, penalties, not-applicable checks, and band thresholds.
- 🟡 Ready to start **Phase 6 — Reporting (Text report format)**.

---

## 2. Implementation Steps

### Phase 1 — Strict MVP Spec ✅ Completed
Rationale: establish deterministic backend capability and a minimal end-to-end path.

**What is completed**
- **Backend (FastAPI)** implemented and tested:
  - `POST /api/audit` accepts CSV (multipart) + optional `target_col`, returns audit JSON.
  - `POST /api/report` returns a downloadable text report.
  - Guardrails: file size cap, encoding fallback.
  - JSON compliance: sanitizer prevents NaN/Inf/numpy scalar serialization errors.

**Note**
- Phase 1 provided backend capabilities for later phases.

---

### Phase 2 — UI Scaffold (Layout + Interaction) ✅ Completed
**Goal**: implement UI layout hierarchy, component structure, and interaction states only.

**Implemented sections (exact order)**
1. Header
2. CSV Upload Area
3. Dataset Preview Table
4. Audit Summary Cards (6)
5. Detailed Audit Panels (6)
6. Modeling Readiness Score Panel
7. Download Report Button

**Implemented interface states**
- Empty state
- Parsing error state
- Audit complete state

**Validation**
- ✅ Frontend E2E testing completed: **26/26 tests passed**.
- ✅ Confirmed constraints: **no sidebar**, **no TOC**, **no charts**, **no animations**.

---

### Phase 3 — Data Ingestion (CSV parsing + preview) ✅ Completed
**Goal**: upload a CSV, parse safely, preserve raw values for later audit, and show a reliable preview with user-friendly errors.

#### Phase 3A — Backend parsing endpoint (`/api/parse`) ✅ Completed
**Why**: separate *parsing/preview* from *audit computation* so ingestion is stable and testable.

**Implemented endpoint**
- `POST /api/parse` (multipart form upload)
  - Input: `file` (CSV only)
  - Output: `ParseResult` JSON

**1) File validation rules (implemented)**
- Extension must be `.csv` (case-insensitive). Hard reject otherwise.
- Size limit enforced (50MB) with HTTP `413`.
- Empty file rejected.
- MIME is treated as a **soft** check (browser-provided and unreliable): clearly binary types are rejected.

**2) Parsing steps (implemented)**
- Read bytes.
- Encoding detection with fallback chain:
  - `utf-8` → `utf-8-sig` → `latin-1` → `cp1252`.
- Delimiter detection:
  - `csv.Sniffer` on first 8KB, fallback to comma.
- Safe parsing via pandas with guardrails:
  - `dtype=str` (preserves raw values; no normalization/enrichment).
  - malformed rows are skipped with warnings.
  - structured parse errors thrown if too many rows appear malformed.

**3) Data structures produced after parsing (implemented)**
- `ParseResult`:
  - `meta`: `filename`, `rows`, `cols`, `column_names`, `encoding`, `delimiter`, `preview_rows_shown`
  - `preview`: first N rows (JSON-safe list of records, **raw string values**)
  - `column_info`: list of `{ name, sample_values }`
  - `warnings`: list of human-readable warnings (encoding, delimiter, skipped malformed rows)

**4) Error handling behavior (implemented)**
- `/api/parse` returns structured errors:
  - `parse_error: true`
  - `code`, `message`, `hint`
  - appropriate HTTP status codes (400/413/422/500)

**5) What is exposed to the audit engine**
- No persistence is introduced.
- Frontend retains the selected file in memory and re-uploads it for the audit step.

**6) Dataset preview behavior**
- Preview displays **raw string values** from parse step.
- Shows meta (rows/cols) plus encoding/delimiter badges when relevant.
- Displays parse warnings banner when present.

#### Phase 3B — Frontend two-step ingestion flow ✅ Completed
**Goal**: implement two-step ingestion without adding preprocessing or extra features.

**Implemented state machine**
- `empty` → `file_selected` → `uploading` → `parsed` → `auditing` → `complete`
- Error branches:
  - `uploading` → `parse_error`
  - `auditing` → `audit_error` (retains parsed preview so user can retry)

**Implemented UI behavior**
- Client-side validation on file select:
  - `.csv` only
  - size limit
  - non-empty
- Buttons:
  - Primary: **Upload & Preview** (calls `/api/parse`)
  - Secondary: **Run Full Audit** (enabled only after successful parse; calls `/api/audit`)
- Preview section:
  - locked/empty instructions in `empty/file_selected`
  - skeleton in `uploading/auditing`
  - real preview + warnings in `parsed/complete`
- Error surface:
  - user-friendly messages + actionable hints

---

### Phase 4 — Audit Engine (Rule-based checks) ✅ Completed
**Goal**: given a parsed CSV dataset (raw values preserved) and an optional selected target column, compute a structured dataset quality audit.

#### Phase 4A — Backend audit engine module ✅ Completed
- Implemented `backend/audit_engine.py`:
  - Deterministic, rule-based checks.
  - Operates on **raw string values** (`dtype=str` DataFrame).
  - No ML models, no external APIs, no fuzzy matching, no preprocessing.
  - Each module returns `applicable: bool` and clear `reason` when not applicable.

**Implemented audit modules (outputs grouped as required)**
- `schema`:
  - row count / column count
  - per-column `unique_count`, `null_count`, `null_pct`, `all_missing`
  - type inference: `numeric` / `categorical` / `datetime` / `text` / `empty`
  - mismatch warnings (`mismatch_columns`) when a text column is mostly numeric
- `missingness`:
  - total missing cells, overall missing %, rows with missing
  - per-column null % and suggested action
- `duplicates`:
  - exact duplicate count and %
  - `applicable: false` for single-column datasets
  - risk label: Low / Moderate / High
- `outliers`:
  - IQR-only detection per inferred numeric column
  - outputs `q1`, `q3`, `iqr`, bounds, outlier count and %
  - `applicable: false` when no numeric columns
- `imbalance`:
  - for selected `target_col`: class counts/pcts, majority-to-minority ratio
  - label: **Balanced / Moderate imbalance / Severe imbalance**
  - `not applicable` if target missing, not selected, or too many unique values (>20)
- `leakage`:
  - leakage keyword heuristics with expanded list:
    `id,target,label,outcome,status,result,final,prediction,future,post,completed,discharge`

**Edge cases handled**
- empty dataset
- single-column dataset
- all-missing column
- non-numeric dataset
- target column not selected / not found
- target column with too many unique values

#### Phase 4B — Backend API integration ✅ Completed
- Updated `POST /api/audit` to:
  - parse via Phase 3 `parse_csv_bytes()` (robust encoding/delimiter handling)
  - run audit via `audit_engine.run_audit(df_raw, target_col=...)`
  - compute readiness score (Phase 5 logic) from module results
  - return structured result object grouped by: `schema, missingness, duplicates, outliers, imbalance, leakage`

#### Phase 4C — Frontend integration ✅ Completed
- Updated `AuditSummaryCards` and `AuditPanels` to consume new field names.
- Added **target column selector** (shadcn Select) within the Class Imbalance panel.
  - Selecting a target column triggers re-run of `/api/audit` with `target_col`.

**Validation**
- Backend Phase 4 checks: **100% pass rate**.
- UI renders all 6 modules correctly and handles `not applicable` reasons.

---

### Phase 5 — Scoring (Weights + thresholds) ✅ Completed
**Goal**: convert audit findings into a transparent modeling readiness score from 0 to 100.

**Implemented scoring method (spec-aligned)**
- Start `score = 100` and subtract deterministic penalties.
- Implemented penalties for:
  1. Missingness
  2. Duplicates
  3. Datatype anomalies
  4. Outliers
  5. Class imbalance
  6. Leakage-risk columns
  7. Basic schema quality issues

**Penalty rules implemented exactly as specified**
- Missingness:
  - ≤1%: 0
  - >1% to 5%: -5
  - >5% to 10%: -10
  - >10%: -20
- Duplicates:
  - 0%: 0
  - >0% to 1%: -5
  - >1% to 3%: -10
  - >3%: -15
- Datatype anomalies:
  - 1–2 anomalies: -5
  - 3–5 anomalies: -10
  - >5 anomalies: -15
- Outliers:
  - no numeric column above 10% outliers: 0
  - any numeric column above 10% outliers: -5
  - any numeric column above 20% outliers: -10
- Class imbalance:
  - balanced: 0
  - moderate imbalance: -5
  - severe imbalance: -10
- Leakage-risk columns:
  - one or more flagged columns: -10
- Basic schema quality:
  - empty dataset: -40
  - missing header names: -10
  - zero-column or zero-row case: -40

**Outputs returned (implemented)**
- `score` (0–100, rounded to 1 decimal)
- `score_band` (4 bands):
  - Ready
  - Acceptable with preprocessing
  - Needs preprocessing
  - High risk
- `penalties`: list of `{ check, penalty, rule }`
- `not_applicable`: list of `{ check, reason }`
- `explanation`: short human-readable summary

**Frontend updates (implemented)**
- Readiness panel displays:
  - score
  - score band badge
  - explanation
  - penalty breakdown list
  - not-applicable checks
  - score-band reference table

**Validation**
- ✅ Phase 5 tests: **100% pass rate** (backend + frontend).

---

### Phase 6 — Reporting (Text report format) 🟡 Next
**Goal**: finalize and validate report formatting and download behavior.

**Planned tasks**
- Ensure downloaded `.txt` matches on-screen section order and naming.
- Include parse metadata (encoding/delimiter) and module applicability reasons.
- Ensure the report includes:
  - schema details
  - missingness
  - duplicates
  - IQR outliers
  - class imbalance (if applicable)
  - leakage flags
  - readiness score, **score_band**, explanation, penalties, and not-applicable checks
- Add an automated regression test to validate report contents for:
  - score_band presence
  - explanation presence
  - penalties list formatting
  - not-applicable checks formatting

---

### Phase 7 — Polish (Non-goals + consistency pass) ⚪ Not Started
**Goal**: consistency, edge-case handling, and guardrails without scope creep.

**Planned tasks**
- Verify forbidden features are not introduced:
  - auth, DB, cloud persistence, Excel, PDF, training, settings pages, workflow builders, multi-dataset sessions.
- UI consistency:
  - typography hierarchy, spacing, consistent labels
  - accessibility (labels, focus rings, semantic table structure)
- Performance guardrails:
  - cap preview rows
  - avoid UI freezing with large datasets

---

## 3. Next Actions
1. Begin **Phase 6 — Reporting**:
   - lock report template headings and section order
   - ensure score band, explanation, penalties, and not-applicable checks are included
2. Add Phase 6 regression tests:
   - confirm report includes all modules and readiness scoring fields
3. Begin Phase 7 prep:
   - consistency pass on copy, labels, and edge case messaging

---

## 4. Success Criteria
- ✅ Phase 2 success criteria met.
- ✅ Phase 3 success criteria met:
  - CSV-only ingestion is reliable with clear validation.
  - Preview consistently displays first N parsed rows and column headers.
  - Malformed rows and encoding issues are handled gracefully with user-friendly errors/warnings.
  - Parsed output is JSON-safe and stable.
  - Audit engine input remains stateless (file re-uploaded; no persistence).
- ✅ Phase 4 success criteria met:
  - All 6 audit modules populate both summary cards and detailed panels.
  - Modules are deterministic and do not apply preprocessing.
  - All checks handle edge cases and expose `applicable` + `reason` when not applicable.
  - UI values match backend computations deterministically.
- ✅ Phase 5 success criteria met:
  - Readiness score is stable, conservative, and explainable.
  - Penalties follow the exact threshold rules.
  - Score bands map correctly to the required labels.
  - No penalties applied for modules marked not applicable.
- Phase 6 success criteria:
  - Downloaded report matches on-screen sections and includes score_band + explanation.
  - Report includes penalties and not-applicable checks in a readable format.
  - Report generation is deterministic and handles edge cases gracefully.

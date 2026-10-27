# DataLens Learning Guide for Future Study

This guide provides a structured walkthrough of DataLens for software engineering interview preparation and architecture study.

---

## Stage 1: Application Architecture & Startup
- **Backend entry**: Check [`backend/app/main.py`](file:///home/gaurang/Desktop/DataLens/backend/app/main.py). It registers routers under `/api`, activates CORS middleware, and calls `init_db()` to automatically create SQLAlchemy tables if they do not exist.
- **Frontend entry**: Check [`frontend/src/main.jsx`](file:///home/gaurang/Desktop/DataLens/frontend/src/main.jsx) and [`frontend/src/App.jsx`](file:///home/gaurang/Desktop/DataLens/frontend/src/App.jsx). Vite proxies `/api` requests directly to `http://127.0.0.1:8000` via `vite.config.js`.

---

## Stage 2: Safe File Ingestion
- Open [`backend/app/services/storage_service.py`](file:///home/gaurang/Desktop/DataLens/backend/app/services/storage_service.py).
- Notice how `save_file_stream` consumes bytes chunk-by-chunk up to a maximum limit (50MB) and aborts with HTTP 413 if the limit is exceeded, preventing server Denial-of-Service (DoS) from unbounded file uploads.
- The stored file is given a UUID name inside `storage/<dataset_id>/`, never using user input as a directory path (preventing path traversal).

---

## Stage 3: Statistical Profiling and Type Inference
- Open [`backend/app/engine/profiler.py`](file:///home/gaurang/Desktop/DataLens/backend/app/engine/profiler.py).
- Notice `infer_column_type`:
  - It avoids blindly converting zero-padded codes (like `"00123"`) to numbers, preserving leading zero semantics.
  - Computes exact duplicate row counts, missing percentages, and numeric dispersion (mean, median, standard deviation).
  - Open [`backend/app/utils/serialization.py`](file:///home/gaurang/Desktop/DataLens/backend/app/utils/serialization.py): Note how Python `NaN`, `Infinity`, and NumPy types are recursively sanitized into standard JSON-compatible values before transmission to the browser.

---

## Stage 4: Non-Destructive Cleaning Engine
- Open [`backend/app/engine/cleaning_engine.py`](file:///home/gaurang/Desktop/DataLens/backend/app/engine/cleaning_engine.py).
- All transformations (imputation, deduplication, casing normalization, outlier clipping, and filtering) operate on explicit function arguments and return `Tuple[pd.DataFrame, Dict[str, Any]]`.
- Notice there is **no arbitrary code execution** (`eval` or `exec`): operations use a strict dictionary dispatcher.

---

## Stage 5: Version Control & Atomic Undo
- Look at `create_new_version` and `undo_last_operation` in [`backend/app/services/dataset_service.py`](file:///home/gaurang/Desktop/DataLens/backend/app/services/dataset_service.py).
- The original file `v1_...` is **never overwritten**. Each operation produces `v2`, `v3`, etc.
- When `undo` is triggered, the pointer `latest_version_id` moves to the parent version without deleting records, guaranteeing auditability.

---

## Stage 6: Server-Side Chart Aggregation
- Open [`backend/app/visualization/chart_service.py`](file:///home/gaurang/Desktop/DataLens/backend/app/visualization/chart_service.py).
- Instead of sending megabytes of raw CSV rows to the client, the backend calculates group-by aggregations (average, count, sum) or histogram bins in Pandas and sends only the aggregated categories and coordinates to Apache ECharts.

---

## Stage 7: Security & Formula Injection Defense
- Open [`backend/app/services/export_service.py`](file:///home/gaurang/Desktop/DataLens/backend/app/services/export_service.py).
- Look at `sanitize_spreadsheet_cell`: cells starting with `=, +, -, @` are prepended with `'` so spreadsheet engines (Excel, LibreOffice) do not evaluate them as dangerous macros or DDE commands.

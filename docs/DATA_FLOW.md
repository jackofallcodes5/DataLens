# DataLens Data Flow

This document details the lifecycle of data through DataLens:

```
[ User Upload (CSV/XLSX) ]
           |
           v
[ 1. Validation & Stream Save ] ──> Writes file chunk by chunk to `storage/<dataset_id>/v1_raw_...`
           |
           v
[ 2. Metadata Persistence ] ────> Inserts row into `datasets` and `dataset_versions` (v1)
           |
           v
[ 3. Profiling & Detection ] ───> `DataProfiler` calculates missing counts, types, IQR bounds.
           |                      `IssueDetector` flags duplicates, invalid emails, empty cols.
           v
[ 4. Simulation & Preview ] ────> `POST /clean/preview` performs transformation in-memory on a copy.
           |                      Returns before-and-after sample diffs to the client.
           v
[ 5. Transformation Commit ] ───> `POST /clean/apply` runs transformation via `CleaningEngine`.
           |                      Writes new version file to disk `v2_....csv`.
           |                      Appends entry to `cleaning_operations`.
           |                      Updates `latest_version_id` in `datasets`.
           v
[ 6. Visualization ] ───────────> `POST /charts/data` aggregates data server-side (sum, avg, count, hist)
           |                      Returns category lists and series points formatted for Apache ECharts.
           v
[ 7. Export ] ──────────────────> `GET /export` sanitizes spreadsheet injection formulas
                                  Streams CSV, XLSX (via OpenPyXL), or JSON quality audit report.
```

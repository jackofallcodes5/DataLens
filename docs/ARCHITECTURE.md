# DataLens Architecture

DataLens is designed as a **Modular Monolith** containing clean boundaries between frontend client presentation, backend API routing, database metadata persistence, filesystem-based dataset storage, and specialized computation engines (profiling, cleaning, visualization, export).

```
                                      [ React + Vite Frontend ]
                                                  |
                                             HTTP / JSON
                                                  v
                                      [ FastAPI Modular Backend ]
                                                  |
           +--------------------+-----------------+--------------------+--------------------+
           |                    |                 |                    |                    |
           v                    v                 v                    v                    v
  [ Database (SQLite/PG) ] [ Storage ]   [ Profiling Engine ]  [ Cleaning Engine ] [ Chart / Export Engine ]
   - projects               - datasets/    - type inference      - deduplication     - ECharts aggregation
   - datasets               - versions/    - IQR outliers        - missing values    - XLSX / CSV streams
   - dataset_versions                      - missing statistics  - normalizations    - Injection mitigation
   - cleaning_operations                   - data issues         - type conversions
   - charts                                                      - undo/versions
```

## Key Architectural Principles

1. **Separation of Concerns**:
   - `app/api/routes`: Exposes REST endpoints, validates HTTP queries and payload structures.
   - `app/services`: Orchestrates transactions between filesystem storage and relational metadata.
   - `app/engine`: Independent, pure data-processing transformations utilizing Pandas and NumPy without side-effects on database models.
   - `app/visualization`: Computes server-side aggregations for ECharts to minimize network transfer.

2. **Immutable Dataset Versions**:
   - The original uploaded dataset is written directly to disk and never mutated in place.
   - Any cleaning transformation creates a new sibling file with atomic file operations (`.tmp` write followed by `os.replace`), advancing `version_number` and keeping full parent-child lineage.
   - Undo transitions the `latest_version_id` pointer back to the parent version without destroying data history.

3. **Formula Injection & Security Mitigations**:
   - File uploads are validated by content structure and limited to 50MB.
   - Internal filesystem storage uses randomized UUID names to avoid path traversal.
   - All spreadsheet exports (CSV and XLSX) escape formula injection triggers (`=`, `+`, `-`, `@`).

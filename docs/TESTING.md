# DataLens Testing Guide

DataLens includes end-to-end integration tests and unit tests verifying the full workflow from upload, profiling, issue detection, preview, cleaning, versioning, undo, chart data generation, and file exports.

---

## Running Backend Tests

Navigate to the `backend/` directory and execute with pytest:

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests/test_integration.py -v
```

### What is Tested:
1. `test_health`: Confirms service health and storage accessibility.
2. `test_full_workflow`:
   - Valid CSV file upload and metadata inspection.
   - Paginated preview.
   - Comprehensive profile computation (missing counts, duplicates).
   - Issue detector verification.
   - Cleaning preview (simulation without data corruption).
   - Cleaning application (deduplication creating version 2).
   - Missing value imputation (filling Salary with median creating version 3).
   - Verification that missing count dropped to 0.
   - Atomic Undo restoring version 2 and recovering previous state.
   - ECharts grouping aggregation calculation (average salary by department).
   - Automatic chart recommendation generation.
   - Chart configuration persistence.
   - CSV export streaming.
   - Excel (.xlsx) export streaming with column width fitting.
   - JSON quality audit report generation.

---

## Testing Frontend Production Build

Navigate to the `frontend/` directory and test the production bundle:

```bash
cd frontend
npm run build
```
Generates verified minified assets into `dist/`.

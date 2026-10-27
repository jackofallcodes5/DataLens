# DataLens Enterprise ETL Pipeline Reference

The ETL subsystem provides automated extraction, pandas data transformations, strict multi-rule record validation, idempotent loading to PostgreSQL/SQLite, an audit Dead Letter Queue (DLQ), and a zero-duplicate retry mechanism.

---

## 🏗️ Architecture

```
                               [ Raw CSV File ]
                                      │
                                      ▼
                        [ 1. EXTRACT: Pandas Engine ]
                       - Auto delimiter (comma, tab, semi)
                       - Header normalization
                                      │
                                      ▼
                      [ 2. TRANSFORM: Cleaning Rules ]
                       - Alias mapping (emp_id -> employee_id)
                       - Null string normalization ("NA", "null" -> None)
                       - Text whitespace trimming
                       - Multi-format datetime parsing
                                      │
                                      ▼
                      [ 3. VALIDATE: Per-Record Rules ]
                       - Schema validation (Pydantic models)
                       - Domain checks (Positive salary, valid email)
                                      │
                       ┌──────────────┴──────────────┐
                       │                             │
                   [ VALID ]                     [ INVALID ]
                       │                             │
                       ▼                             ▼
              [ 4. LOAD: Upsert ]         [ 5. REJECT: Dead Letter Queue ]
          - PostgreSQL / SQLite            - Logged to `etl_record_logs`
          - Natural key deduplication      - Status = 'REJECTED'
          - Hash tracking                  - Rejection reason captured
                       │                             │
                       └──────────────┬──────────────┘
                                      │
                                      ▼
                            [ 6. RETRY ENGINE ]
                       - Load corrected records
                       - Idempotent upsert
                       - Status updated to 'RETRIED'
                       - Zero duplicate rows
```

---

## 📋 Database Tables

1. **`etl_employees`** (Target Production Table):
   - `employee_id` (Integer, Primary Key)
   - `name` (String, Non-null)
   - `department` (String, Non-null, Indexed)
   - `salary` (Float, Non-null)
   - `joining_date` (Date, Non-null)
   - `email` (String, Unique, Indexed)
   - `record_hash` (SHA256 checksum)
   - `etl_batch_id` (String, Execution batch identifier)
   - `loaded_at`, `updated_at` (Timestamps)

2. **`etl_job_runs`** (Batch Execution Auditing):
   - `batch_id` (Primary Key)
   - `source_file` (Filename)
   - `status` (`COMPLETED`, `COMPLETED_WITH_FAILURES`, `FAILED`)
   - `total_records`, `successful_records`, `rejected_records`
   - `started_at`, `completed_at`

3. **`etl_record_logs`** (Dead Letter Queue & Record Auditing):
   - `id` (Auto-increment Primary Key)
   - `batch_id` (Batch ID)
   - `raw_record_identifier` (e.g. Employee ID)
   - `status` (`SUCCESS`, `REJECTED`, `RETRIED`)
   - `rejection_reason` (Detailed validation failure message)
   - `raw_payload_json` (Original input data)
   - `processed_payload_json` (Loaded output data if successful)
   - `logged_at` (Timestamp)

---

## 🚀 How to Run the Pipeline

### Option 1: Python CLI / Script
```python
from app.etl.pipeline import ETLPipeline

with ETLPipeline() as pipeline:
    summary = pipeline.run_pipeline("sample_data/employees_sample.csv")
    print("ETL Result:", summary)
```

### Option 2: REST API
1. Run a CSV through the pipeline:
   ```bash
   curl -X POST http://localhost:8000/api/etl/run-csv \
     -F "file=@sample_data/employees_sample.csv"
   ```

2. Inspect batch execution runs:
   ```bash
   curl http://localhost:8000/api/etl/runs
   ```

3. Query the Dead Letter Queue for rejected records:
   ```bash
   curl http://localhost:8000/api/etl/runs/<BATCH_ID>/logs?status=REJECTED
   ```

4. Retry corrected records without duplicates:
   ```bash
   curl -X POST http://localhost:8000/api/etl/retry \
     -H "Content-Type: application/json" \
     -d '[
       {
         "employee_id": 203,
         "name": "Corrected Employee",
         "department": "Engineering",
         "salary": 90000,
         "joining_date": "2021-04-15",
         "email": "corrected@example.com"
       }
     ]'
   ```

---

## 🔒 Deduplication & Idempotent Retry Guarantee
- Both **PostgreSQL** (`INSERT ... ON CONFLICT (employee_id) DO UPDATE`) and **SQLite** (`ON CONFLICT DO UPDATE`) upsert statements are supported.
- If a failed record is corrected and retried, its existing record in `etl_employees` is updated with the new attributes and batch ID. No secondary rows or duplicate IDs are ever created.
- The previous audit rejection log in `etl_record_logs` is atomically updated from `REJECTED` to `RETRIED`.

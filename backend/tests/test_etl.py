import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from app.main import app
from app.etl.pipeline import ETLPipeline
from app.models.etl_models import ETLEmployee, ETLJobRun, ETLRecordLog
from app.database import SessionLocal, init_db

# Ensure all tables are created
init_db()

client = TestClient(app)

SAMPLE_ETL_CSV = """EmployeeID,Name,Department,Salary,JoiningDate,Email
201,John Doe,Engineering,95000,2022-01-15,john.doe@example.com
202,Jane Smith,Marketing,82000,2021-06-20,jane.smith@example.com
203,Bad Salary,Engineering,-5000,2020-03-11,bad.salary@example.com
204,Bad Email,HR,60000,2023-08-01,not-an-email
205,,Finance,75000,2019-11-04,empty.name@example.com
206,Bob Jones,Engineering,88000,2020-05-12,bob.jones@example.com
"""

def test_etl_pipeline_extraction_transformation_and_loading():
    with tempfile.NamedTemporaryFile("w+", suffix=".csv", delete=False) as tmp:
        tmp.write(SAMPLE_ETL_CSV)
        tmp_path = tmp.name

    try:
        db = SessionLocal()
        pipeline = ETLPipeline(db_session=db)
        summary = pipeline.run_pipeline(tmp_path)

        assert summary["total_records"] == 6
        # Expected: 3 valid (201, 202, 206) and 3 rejected (203 negative salary, 204 invalid email, 205 empty name check or validation)
        assert summary["successful_records"] == 3
        assert summary["rejected_records"] == 3

        # Verify Target Table has only the 3 successful employees
        loaded_count = db.query(ETLEmployee).filter(ETLEmployee.employee_id.in_([201, 202, 206])).count()
        assert loaded_count == 3

        # Verify Dead Letter Queue / Audit logs
        reject_logs = db.query(ETLRecordLog).filter(
            ETLRecordLog.batch_id == summary["batch_id"],
            ETLRecordLog.status == "REJECTED"
        ).all()
        assert len(reject_logs) == 3

        # Confirm rejection reasons were captured
        reasons = [r.rejection_reason for r in reject_logs]
        assert any("Salary must be a strictly positive" in str(r) for r in reasons)
        assert any("Invalid email format" in str(r) for r in reasons)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        db.close()


def test_etl_retry_mechanism_prevents_duplicates():
    """
    Test that retrying corrected records succeeds and does NOT duplicate existing records.
    """
    db = SessionLocal()
    pipeline = ETLPipeline(db_session=db)

    # Corrected version of rejected record 203 (Fixed negative salary from -5000 to 90000)
    corrected_data = [
        {
            "employee_id": 203,
            "name": "Corrected Salary Guy",
            "department": "Engineering",
            "salary": 90000.0,
            "joining_date": "2020-03-11",
            "email": "corrected.salary@example.com"
        }
    ]

    retry_summary = pipeline.retry_rejected_records(corrected_records=corrected_data)
    assert retry_summary["retried_successful"] == 1

    # Verify record 203 is now present in target table
    emp203 = db.query(ETLEmployee).filter(ETLEmployee.employee_id == 203).first()
    assert emp203 is not None
    assert emp203.salary == 90000.0

    # RETRY AGAIN with same data - verifies idempotent UPSERT preventing duplicates
    retry_again = pipeline.retry_rejected_records(corrected_records=corrected_data)
    assert retry_again["retried_successful"] == 1

    # Total count of employee 203 must still be exactly 1
    total_203 = db.query(ETLEmployee).filter(ETLEmployee.employee_id == 203).count()
    assert total_203 == 1

    db.close()


def test_etl_api_endpoints():
    # 1. Run upload through API
    csv_bytes = SAMPLE_ETL_CSV.encode("utf-8")
    res = client.post(
        "/api/etl/run-csv",
        files={"file": ("test_etl_upload.csv", csv_bytes, "text/csv")}
    )
    assert res.status_code == 200
    res_data = res.json()["data"]
    batch_id = res_data["batch_id"]
    assert res_data["total_records"] == 6

    # 2. Query batch audit logs
    res = client.get(f"/api/etl/runs/{batch_id}/logs")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) == 6

    # 3. Query target employees
    res = client.get("/api/etl/employees?department=Engineering")
    assert res.status_code == 200
    emps = res.json()
    assert len(emps) >= 2

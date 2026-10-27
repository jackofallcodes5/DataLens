from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, Body
from sqlalchemy.orm import Session
import os
import tempfile

from app.database import get_db
from app.etl.pipeline import ETLPipeline
from app.models.etl_models import ETLJobRun, ETLRecordLog, ETLEmployee

router = APIRouter(prefix="/etl", tags=["etl"])

@router.post("/run-csv")
def run_etl_from_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Extracts data from uploaded CSV, transforms with pandas, validates each record,
    and loads into the database with full success/failure/rejection logging.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported for this ETL pipeline.")

    # Save to temp file
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        pipeline = ETLPipeline(db_session=db)
        result = pipeline.run_pipeline(tmp_path)
        return {
            "message": "ETL pipeline execution completed.",
            "data": result
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.get("/runs")
def list_etl_runs(db: Session = Depends(get_db)):
    """List historical ETL batch execution runs."""
    runs = db.query(ETLJobRun).order_by(ETLJobRun.started_at.desc()).limit(50).all()
    return runs

@router.get("/runs/{batch_id}/logs")
def get_run_logs(
    batch_id: str,
    status: Optional[str] = Query(None, description="SUCCESS, REJECTED, RETRIED"),
    db: Session = Depends(get_db)
):
    """Retrieve audit logs for a specific ETL execution batch."""
    query = db.query(ETLRecordLog).filter(ETLRecordLog.batch_id == batch_id)
    if status:
        query = query.filter(ETLRecordLog.status == status)
    logs = query.order_by(ETLRecordLog.logged_at.desc()).limit(500).all()
    return logs

@router.get("/employees")
def list_etl_employees(
    department: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Query currently loaded employee records in target table."""
    query = db.query(ETLEmployee)
    if department:
        query = query.filter(ETLEmployee.department == department)
    return query.limit(limit).all()

@router.post("/retry")
def retry_failed_records(
    batch_id: Optional[str] = Query(None),
    corrected_records: Optional[List[Dict[str, Any]]] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Retries rejected or corrected records. Idempotently loads valid records
    into the database without creating duplicate entries.
    """
    pipeline = ETLPipeline(db_session=db)
    result = pipeline.retry_rejected_records(
        batch_id=batch_id,
        corrected_records=corrected_records
    )
    return {
        "message": "Retry operation finished.",
        "data": result
    }

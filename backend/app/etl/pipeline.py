import os
import hashlib
import json
import uuid
import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.etl.validator import validate_record, EmployeeValidatedRecord
from app.models.etl_models import ETLEmployee, ETLJobRun, ETLRecordLog
from app.database import engine, SessionLocal


class ETLPipeline:
    """
    Production-ready ETL Pipeline:
    1. Extract: Extracts records from standard or messy CSVs.
    2. Transform: Standardizes casing, cleans whitespaces, parses flexible dates, handles null representations.
    3. Validate: Validates types and business domain rules per-record before loading.
    4. Load (PostgreSQL/SQLite Upsert): Idempotently loads valid records using natural primary key.
    5. Audit & DLQ (Dead Letter Queue): Logs successful, failed, and rejected records.
    6. Retry: Allows retrying previously rejected records after correction with guaranteed zero duplicate rows.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session or SessionLocal()
        self.is_external_session = db_session is not None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.is_external_session:
            self.db.close()

    # ==========================================
    # 1. EXTRACT
    # ==========================================
    @staticmethod
    def extract_from_csv(file_path: str) -> pd.DataFrame:
        """
        Extracts raw tabular data from a CSV file with automatic delimiter and encoding detection.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source CSV file not found: {file_path}")

        try:
            df = pd.read_csv(file_path, sep=None, engine="python", encoding="utf-8")
        except Exception:
            df = pd.read_csv(file_path, sep=None, engine="python", encoding="latin-1")

        # Standardize column headers: trim spaces and normalize
        df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
        return df

    # ==========================================
    # 2. TRANSFORM
    # ==========================================
    @staticmethod
    def transform_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms the extracted DataFrame:
        - Maps alternate column names
        - Trims whitespace across all string/object columns
        - Normalizes null strings ("NA", "null", "none", "") into NaN
        - Cleans and standardizes dates
        - Coerces numerical values cleanly
        """
        transformed = df.copy()

        # Map common header variations
        col_mappings = {
            "employeeid": "employee_id",
            "emp_id": "employee_id",
            "id": "employee_id",
            "full_name": "name",
            "emp_name": "name",
            "joiningdate": "joining_date",
            "join_date": "joining_date",
            "dept": "department",
            "email_address": "email"
        }
        transformed = transformed.rename(columns=col_mappings)

        # Standardize missing/empty values using clean string stripping & masking
        for col in transformed.columns:
            if transformed[col].dtype == object:
                # Strip string whitespace
                transformed[col] = transformed[col].apply(
                    lambda x: x.strip() if isinstance(x, str) else x
                )
                # Map empty or null-like strings to None
                null_patterns = {"", "null", "none", "nan", "na", "-", "undefined"}
                transformed[col] = transformed[col].apply(
                    lambda x: None if (isinstance(x, str) and x.lower() in null_patterns) else x
                )

        # Clean Dates using pandas flexible parsing
        if "joining_date" in transformed.columns:
            transformed["joining_date"] = pd.to_datetime(
                transformed["joining_date"],
                errors="coerce",
                format="mixed"
            ).dt.date

        return transformed

    # ==========================================
    # 3. COMPUTE RECORD HASH
    # ==========================================
    @staticmethod
    def compute_record_hash(record_dict: Dict[str, Any]) -> str:
        """Generates a reproducible SHA256 checksum of normalized record contents."""
        serialized = json.dumps(record_dict, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    # ==========================================
    # 4. LOAD (UPSERT / IDEMPOTENT INSERTION)
    # ==========================================
    def load_record_upsert(self, validated_record: EmployeeValidatedRecord, batch_id: str) -> None:
        """
        Idempotent database upsert targeting PostgreSQL with SQLite compatibility.
        If employee_id already exists, updates attributes rather than throwing a duplicate key error.
        """
        rec_dict = validated_record.model_dump()
        rec_dict["record_hash"] = self.compute_record_hash(rec_dict)
        rec_dict["etl_batch_id"] = batch_id
        rec_dict["updated_at"] = datetime.datetime.utcnow()

        dialect_name = self.db.bind.dialect.name if self.db.bind else "sqlite"

        if dialect_name == "postgresql":
            # PostgreSQL ON CONFLICT DO UPDATE
            stmt = pg_insert(ETLEmployee).values(**rec_dict)
            stmt = stmt.on_conflict_do_update(
                index_elements=[ETLEmployee.employee_id],
                set_={
                    "name": stmt.excluded.name,
                    "department": stmt.excluded.department,
                    "salary": stmt.excluded.salary,
                    "joining_date": stmt.excluded.joining_date,
                    "email": stmt.excluded.email,
                    "record_hash": stmt.excluded.record_hash,
                    "etl_batch_id": stmt.excluded.etl_batch_id,
                    "updated_at": stmt.excluded.updated_at
                }
            )
            self.db.execute(stmt)
        else:
            # SQLite ON CONFLICT DO UPDATE
            stmt = sqlite_insert(ETLEmployee).values(**rec_dict)
            stmt = stmt.on_conflict_do_update(
                index_elements=[ETLEmployee.employee_id],
                set_={
                    "name": stmt.excluded.name,
                    "department": stmt.excluded.department,
                    "salary": stmt.excluded.salary,
                    "joining_date": stmt.excluded.joining_date,
                    "email": stmt.excluded.email,
                    "record_hash": stmt.excluded.record_hash,
                    "etl_batch_id": stmt.excluded.etl_batch_id,
                    "updated_at": stmt.excluded.updated_at
                }
            )
            self.db.execute(stmt)

    # ==========================================
    # 5. FULL PIPELINE EXECUTION
    # ==========================================
    def run_pipeline(self, csv_file_path: str, batch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes full Extract -> Transform -> Validate -> Load -> Audit cycle.
        """
        batch_id = batch_id or f"batch_{uuid.uuid4().hex[:12]}"
        filename = os.path.basename(csv_file_path)
        started_at = datetime.datetime.utcnow()

        # Initialize Job Run Record
        job_run = ETLJobRun(
            batch_id=batch_id,
            source_file=filename,
            status="RUNNING",
            started_at=started_at
        )
        self.db.add(job_run)
        self.db.commit()

        # Step 1: Extract
        try:
            df_raw = self.extract_from_csv(csv_file_path)
        except Exception as e:
            job_run.status = "FAILED"
            job_run.completed_at = datetime.datetime.utcnow()
            job_run.error_summary = f"Extraction failure: {str(e)}"
            self.db.commit()
            raise

        # Step 2: Transform
        df_transformed = self.transform_dataframe(df_raw)
        records = df_transformed.to_dict(orient="records")
        total_records = len(records)
        job_run.total_records = total_records

        success_count = 0
        rejected_count = 0

        # Steps 3, 4, 5: Validate, Load, and Log
        for rec in records:
            # Sanitize record dict for serialization
            clean_rec = {
                k: (None if pd.isna(v) else v) for k, v in rec.items()
            }
            raw_identifier = str(clean_rec.get("employee_id") or clean_rec.get("email") or "unknown")

            validation_res = validate_record(clean_rec)

            if validation_res.is_valid:
                try:
                    self.load_record_upsert(validation_res.validated_record, batch_id)
                    # Log SUCCESS
                    log_entry = ETLRecordLog(
                        batch_id=batch_id,
                        source_file=filename,
                        raw_record_identifier=raw_identifier,
                        status="SUCCESS",
                        raw_payload_json=json.dumps(clean_rec, default=str),
                        processed_payload_json=json.dumps(validation_res.validated_record.model_dump(), default=str)
                    )
                    self.db.add(log_entry)
                    success_count += 1
                except Exception as db_err:
                    self.db.rollback()
                    # Treat DB load failure as REJECTED record
                    log_entry = ETLRecordLog(
                        batch_id=batch_id,
                        source_file=filename,
                        raw_record_identifier=raw_identifier,
                        status="REJECTED",
                        rejection_reason=f"Database load error: {str(db_err)}",
                        raw_payload_json=json.dumps(clean_rec, default=str)
                    )
                    self.db.add(log_entry)
                    rejected_count += 1
            else:
                # Log REJECTED record (Dead Letter Queue)
                log_entry = ETLRecordLog(
                    batch_id=batch_id,
                    source_file=filename,
                    raw_record_identifier=raw_identifier,
                    status="REJECTED",
                    rejection_reason=validation_res.error_message,
                    raw_payload_json=json.dumps(clean_rec, default=str)
                )
                self.db.add(log_entry)
                rejected_count += 1

        # Finalize Job Run
        job_run.successful_records = success_count
        job_run.rejected_records = rejected_count
        job_run.status = "COMPLETED" if rejected_count == 0 else "COMPLETED_WITH_FAILURES"
        job_run.completed_at = datetime.datetime.utcnow()
        self.db.commit()

        return {
            "batch_id": batch_id,
            "status": job_run.status,
            "source_file": filename,
            "total_records": total_records,
            "successful_records": success_count,
            "rejected_records": rejected_count
        }

    # ==========================================
    # 6. RETRY REJECTED / FAILED RECORDS
    # ==========================================
    def retry_rejected_records(
        self,
        batch_id: Optional[str] = None,
        corrected_records: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Retries failed/rejected records without duplicating existing data:
        1. If corrected_records are provided, re-validates and upserts them.
        2. If none provided, fetches previously REJECTED records for the given batch_id,
           re-evaluates them, and upserts those that are now valid.
        3. Updates previous reject audit logs to status='RETRIED'.
        """
        retry_batch_id = f"retry_{uuid.uuid4().hex[:10]}"
        retried_success = 0
        still_rejected = 0

        if corrected_records:
            records_to_process = corrected_records
        else:
            query = self.db.query(ETLRecordLog).filter(ETLRecordLog.status == "REJECTED")
            if batch_id:
                query = query.filter(ETLRecordLog.batch_id == batch_id)
            reject_logs = query.all()
            records_to_process = [
                (log.id, json.loads(log.raw_payload_json)) for log in reject_logs
            ]

        for item in records_to_process:
            if isinstance(item, tuple):
                original_log_id, raw_rec = item
            else:
                original_log_id, raw_rec = None, item

            # Transform single record
            df_single = pd.DataFrame([raw_rec])
            df_transformed = self.transform_dataframe(df_single)
            transformed_rec = df_transformed.to_dict(orient="records")[0]
            clean_rec = {k: (None if pd.isna(v) else v) for k, v in transformed_rec.items()}

            raw_identifier = str(clean_rec.get("employee_id") or clean_rec.get("email") or "unknown")
            validation_res = validate_record(clean_rec)

            if validation_res.is_valid:
                self.load_record_upsert(validation_res.validated_record, retry_batch_id)
                # Add retry log entry
                log_entry = ETLRecordLog(
                    batch_id=retry_batch_id,
                    source_file="retry_correction",
                    raw_record_identifier=raw_identifier,
                    status="SUCCESS",
                    raw_payload_json=json.dumps(clean_rec, default=str),
                    processed_payload_json=json.dumps(validation_res.validated_record.model_dump(), default=str)
                )
                self.db.add(log_entry)

                # Mark original log as RETRIED
                if original_log_id:
                    orig_log = self.db.query(ETLRecordLog).filter(ETLRecordLog.id == original_log_id).first()
                    if orig_log:
                        orig_log.status = "RETRIED"

                retried_success += 1
            else:
                still_rejected += 1

        self.db.commit()
        return {
            "retry_batch_id": retry_batch_id,
            "retried_successful": retried_success,
            "still_rejected": still_rejected
        }

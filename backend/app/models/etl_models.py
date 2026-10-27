import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    Date,
    Index,
    UniqueConstraint
)
from app.database import Base

class ETLEmployee(Base):
    """
    Target table for processed and validated employee records.
    Natural business primary key is employee_id.
    Upsert logic (idempotent loading) ensures retried records update rather than duplicate.
    """
    __tablename__ = "etl_employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False, index=True)
    salary = Column(Float, nullable=False)
    joining_date = Column(Date, nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    
    # Audit tracking
    record_hash = Column(String(64), nullable=True)
    etl_batch_id = Column(String(64), nullable=False, index=True)
    loaded_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ETLJobRun(Base):
    """
    Logs each execution batch of the ETL pipeline.
    """
    __tablename__ = "etl_job_runs"

    batch_id = Column(String(64), primary_key=True)
    source_file = Column(String(255), nullable=False)
    status = Column(String(30), nullable=False)  # COMPLETED, COMPLETED_WITH_FAILURES, FAILED
    total_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    rejected_records = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_summary = Column(Text, nullable=True)


class ETLRecordLog(Base):
    """
    Detailed audit log tracking each individual record's ETL lifecycle:
    Records status ('SUCCESS', 'REJECTED', 'RETRIED') and validation failure details.
    """
    __tablename__ = "etl_record_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), index=True, nullable=False)
    source_file = Column(String(255), nullable=False)
    raw_record_identifier = Column(String(100), nullable=True, index=True)
    status = Column(String(30), nullable=False, index=True)  # SUCCESS, REJECTED, RETRIED
    rejection_reason = Column(Text, nullable=True)
    raw_payload_json = Column(Text, nullable=False)
    processed_payload_json = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("idx_batch_status", "batch_id", "status"),
    )

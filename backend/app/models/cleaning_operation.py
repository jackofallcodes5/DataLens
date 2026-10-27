import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class CleaningOperation(Base):
    __tablename__ = "cleaning_operations"

    id = Column(String(36), primary_key=True, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    input_version_id = Column(String(36), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False)
    output_version_id = Column(String(36), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=True)
    operation_type = Column(String(50), nullable=False)
    parameters_json = Column(Text, nullable=False)
    result_summary_json = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, success, failed, undone
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    dataset = relationship("Dataset", back_populates="operations")

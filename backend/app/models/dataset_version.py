import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(String(36), primary_key=True, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    parent_version_id = Column(String(36), ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True)
    operation_type = Column(String(50), default="initial_upload")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    metadata_json = Column(Text, nullable=True)  # Store row_count, col_count, column_names as JSON

    # Relationships
    dataset = relationship("Dataset", back_populates="versions", foreign_keys=[dataset_id])

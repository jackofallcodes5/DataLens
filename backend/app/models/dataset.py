import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_format = Column(String(20), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    latest_version_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="datasets")
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan", foreign_keys="DatasetVersion.dataset_id")
    operations = relationship("CleaningOperation", back_populates="dataset", cascade="all, delete-orphan")
    charts = relationship("Chart", back_populates="dataset", cascade="all, delete-orphan")

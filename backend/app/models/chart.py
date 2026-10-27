import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Chart(Base):
    __tablename__ = "charts"

    id = Column(String(36), primary_key=True, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id = Column(String(36), ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    chart_type = Column(String(50), nullable=False)
    configuration_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="charts")
    dataset = relationship("Dataset", back_populates="charts")

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dataset_service import DatasetService
from app.services.storage_service import StorageService
from app.engine.profiler import DataProfiler
from app.engine.issue_detector import IssueDetector
from app.utils.serialization import clean_for_json

router = APIRouter(prefix="/datasets", tags=["profiling"])

@router.get("/{dataset_id}/profile")
def get_profile(
    dataset_id: str,
    version_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    version = DatasetService.get_version(db, dataset_id, version_id)
    df = StorageService.read_dataframe(version.storage_path)
    profile = DataProfiler.profile_dataframe(df)
    return clean_for_json(profile)

@router.get("/{dataset_id}/issues")
def get_issues(
    dataset_id: str,
    version_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    version = DatasetService.get_version(db, dataset_id, version_id)
    df = StorageService.read_dataframe(version.storage_path)
    issues = IssueDetector.detect_issues(df)
    return clean_for_json(issues)

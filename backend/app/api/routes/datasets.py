from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.schemas.schemas import DatasetResponse, DatasetVersionResponse, DatasetPreviewResponse
from app.services.dataset_service import DatasetService
from app.services.storage_service import StorageService
from app.utils.file_validation import validate_upload_file, sanitize_filename
from app.config import settings

router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.get("", response_model=List[DatasetResponse])
def list_datasets(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Dataset)
    if project_id:
        query = query.filter(Dataset.project_id == project_id)
    return query.order_by(Dataset.created_at.desc()).all()

@router.post("", response_model=DatasetResponse, status_code=201)
def upload_dataset(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    validate_upload_file(file, settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024)
    clean_name = sanitize_filename(file.filename)
    dataset = DatasetService.create_dataset_from_upload(
        db=db,
        filename=clean_name,
        file_obj=file.file,
        project_id=project_id
    )
    return dataset

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    return DatasetService.get_dataset(db, dataset_id)

@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    dataset = DatasetService.get_dataset(db, dataset_id)
    StorageService.delete_dataset_files(dataset.id)
    db.delete(dataset)
    db.commit()
    return {"status": "success", "message": f"Dataset '{dataset_id}' deleted."}

@router.get("/{dataset_id}/versions", response_model=List[DatasetVersionResponse])
def list_versions(dataset_id: str, db: Session = Depends(get_db)):
    DatasetService.get_dataset(db, dataset_id)
    return db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id
    ).order_by(DatasetVersion.version_number.desc()).all()

@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def get_preview(
    dataset_id: str,
    version_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return DatasetService.get_preview(
        db=db,
        dataset_id=dataset_id,
        version_id=version_id,
        page=page,
        page_size=page_size
    )

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dataset_service import DatasetService
from app.services.storage_service import StorageService
from app.engine.cleaning_engine import CleaningEngine
from app.models.cleaning_operation import CleaningOperation
from app.schemas.schemas import (
    CleaningOperationRequest,
    CleaningPreviewResponse,
    CleaningApplyResponse,
    HistoryItemResponse,
    DatasetVersionResponse
)
from app.utils.serialization import clean_for_json

router = APIRouter(prefix="/datasets", tags=["cleaning"])

@router.post("/{dataset_id}/clean/preview", response_model=CleaningPreviewResponse)
def preview_cleaning(
    dataset_id: str,
    req: CleaningOperationRequest,
    version_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    version = DatasetService.get_version(db, dataset_id, version_id)
    df = StorageService.read_dataframe(version.storage_path)

    # Execute transformation on a copy in-memory only (does NOT modify file)
    df_preview, summary = CleaningEngine.apply_operation(df, req.operation_type, req.parameters)

    # Generate sample diff (first 5 rows)
    sample_before = clean_for_json(df.head(5).to_dict(orient="records"))
    sample_after = clean_for_json(df_preview.head(5).to_dict(orient="records"))

    affected_cols = summary.get("columns") or [summary.get("column")] if summary.get("column") else []
    if "removed_columns" in summary:
        affected_cols = summary["removed_columns"]

    warnings = []
    if len(df_preview) == 0:
        warnings.append("Warning: This operation will remove ALL rows from the dataset.")

    return {
        "operation_type": req.operation_type,
        "expected_rows": len(df_preview),
        "expected_columns": len(df_preview.columns),
        "rows_affected": abs(len(df) - len(df_preview)),
        "columns_affected": affected_cols,
        "sample_before": sample_before,
        "sample_after": sample_after,
        "warnings": warnings
    }

@router.post("/{dataset_id}/clean/apply", response_model=CleaningApplyResponse)
def apply_cleaning(
    dataset_id: str,
    req: CleaningOperationRequest,
    db: Session = Depends(get_db)
):
    dataset = DatasetService.get_dataset(db, dataset_id)
    current_version = DatasetService.get_version(db, dataset_id, dataset.latest_version_id)
    df = StorageService.read_dataframe(current_version.storage_path)

    # Execute transformation
    df_cleaned, summary = CleaningEngine.apply_operation(df, req.operation_type, req.parameters)

    # Persist as a new dataset version
    new_version = DatasetService.create_new_version(
        db=db,
        dataset=dataset,
        current_version=current_version,
        new_df=df_cleaned,
        op_type=req.operation_type,
        op_params=req.parameters,
        summary=summary
    )

    return {
        "success": True,
        "new_version_id": new_version.id,
        "new_version_number": new_version.version_number,
        "summary": summary
    }

@router.get("/{dataset_id}/history", response_model=List[HistoryItemResponse])
def get_cleaning_history(dataset_id: str, db: Session = Depends(get_db)):
    DatasetService.get_dataset(db, dataset_id)
    ops = db.query(CleaningOperation).filter(
        CleaningOperation.dataset_id == dataset_id
    ).order_by(CleaningOperation.created_at.desc()).all()

    results = []
    for op in ops:
        params = json.loads(op.parameters_json) if op.parameters_json else {}
        summary = json.loads(op.result_summary_json) if op.result_summary_json else {}
        results.append({
            "id": op.id,
            "operation_type": op.operation_type,
            "parameters": params,
            "result_summary": summary,
            "status": op.status,
            "error_message": op.error_message,
            "created_at": op.created_at
        })
    return results

@router.post("/{dataset_id}/undo", response_model=DatasetVersionResponse)
def undo_cleaning(dataset_id: str, db: Session = Depends(get_db)):
    parent_version = DatasetService.undo_last_operation(db, dataset_id)
    return parent_version

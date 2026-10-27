import json
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cleaning_operation import CleaningOperation
from app.services.dataset_service import DatasetService
from app.services.storage_service import StorageService
from app.services.export_service import ExportService

router = APIRouter(prefix="/datasets", tags=["exports"])

@router.get("/{dataset_id}/export")
def export_dataset(
    dataset_id: str,
    format: str = Query("csv", regex="^(csv|xlsx|report)$"),
    version_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    dataset = DatasetService.get_dataset(db, dataset_id)
    version = DatasetService.get_version(db, dataset_id, version_id)
    df = StorageService.read_dataframe(version.storage_path)

    base_name = f"{dataset.original_filename.rsplit('.', 1)[0]}_v{version.version_number}"

    if format == "csv":
        return ExportService.export_csv_stream(df, base_name)
    elif format == "xlsx":
        return ExportService.export_excel_stream(df, base_name)
    elif format == "report":
        # Compile cleaning history
        ops = db.query(CleaningOperation).filter(
            CleaningOperation.dataset_id == dataset_id
        ).order_by(CleaningOperation.created_at.asc()).all()
        history = [
            {
                "operation": op.operation_type,
                "summary": json.loads(op.result_summary_json) if op.result_summary_json else {},
                "status": op.status,
                "time": str(op.created_at)
            }
            for op in ops
        ]
        return ExportService.export_quality_report_json(
            df=df,
            dataset_name=dataset.original_filename,
            version_num=version.version_number,
            history=history
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format.")

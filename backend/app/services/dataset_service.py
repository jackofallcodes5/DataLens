import uuid
import json
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.cleaning_operation import CleaningOperation
from app.services.storage_service import StorageService
from app.utils.serialization import clean_for_json

class DatasetService:
    @staticmethod
    def get_dataset(db: Session, dataset_id: str) -> Dataset:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
        return dataset

    @staticmethod
    def get_version(db: Session, dataset_id: str, version_id: Optional[str] = None) -> DatasetVersion:
        if version_id:
            version = db.query(DatasetVersion).filter(
                DatasetVersion.id == version_id,
                DatasetVersion.dataset_id == dataset_id
            ).first()
        else:
            dataset = DatasetService.get_dataset(db, dataset_id)
            version = db.query(DatasetVersion).filter(
                DatasetVersion.id == dataset.latest_version_id
            ).first()

        if not version:
            raise HTTPException(status_code=404, detail="Dataset version not found.")
        return version

    @staticmethod
    def create_dataset_from_upload(
        db: Session,
        filename: str,
        file_obj,
        project_id: Optional[str] = None
    ) -> Dataset:
        dataset_id = str(uuid.uuid4())
        
        # Stream save file to storage
        storage_path, file_size = StorageService.save_file_stream(dataset_id, file_obj, filename)
        file_format = filename.split(".")[-1].lower()

        # Parse dataframe to inspect metadata
        try:
            df = StorageService.read_dataframe(storage_path)
        except Exception as e:
            StorageService.delete_dataset_files(dataset_id)
            raise e

        row_count = len(df)
        column_count = len(df.columns)
        columns_list = list(df.columns)

        version_id = str(uuid.uuid4())
        metadata_json = json.dumps({
            "columns": columns_list,
            "row_count": row_count,
            "column_count": column_count
        })

        # Create initial Version
        version = DatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            version_number=1,
            storage_path=storage_path,
            parent_version_id=None,
            operation_type="initial_upload",
            metadata_json=metadata_json
        )

        dataset = Dataset(
            id=dataset_id,
            project_id=project_id,
            original_filename=filename,
            storage_path=storage_path,
            file_format=file_format,
            file_size=file_size,
            row_count=row_count,
            column_count=column_count,
            latest_version_id=version_id
        )

        db.add(dataset)
        db.add(version)
        db.commit()
        db.refresh(dataset)
        return dataset

    @staticmethod
    def get_preview(
        db: Session,
        dataset_id: str,
        version_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        version = DatasetService.get_version(db, dataset_id, version_id)
        df = StorageService.read_dataframe(version.storage_path)

        total_rows = len(df)
        total_columns = len(df.columns)
        columns = list(df.columns)

        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_df = df.iloc[start_idx:end_idx]

        # Convert to dictionary with None for NaN/Inf
        rows = [clean_for_json(row) for row in page_df.to_dict(orient="records")]

        return {
            "dataset_id": dataset_id,
            "version_id": version.id,
            "version_number": version.version_number,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "columns": columns,
            "rows": rows,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    def create_new_version(
        db: Session,
        dataset: Dataset,
        current_version: DatasetVersion,
        new_df: pd.DataFrame,
        op_type: str,
        op_params: Dict[str, Any],
        summary: Dict[str, Any]
    ) -> DatasetVersion:
        new_version_num = current_version.version_number + 1
        new_version_id = str(uuid.uuid4())

        # Save new dataframe file
        new_path = StorageService.save_version_dataframe(dataset.id, new_version_num, new_df)

        meta = json.dumps({
            "columns": list(new_df.columns),
            "row_count": len(new_df),
            "column_count": len(new_df.columns)
        })

        new_version = DatasetVersion(
            id=new_version_id,
            dataset_id=dataset.id,
            version_number=new_version_num,
            storage_path=new_path,
            parent_version_id=current_version.id,
            operation_type=op_type,
            metadata_json=meta
        )

        # Record operation
        cleaning_op = CleaningOperation(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            input_version_id=current_version.id,
            output_version_id=new_version_id,
            operation_type=op_type,
            parameters_json=json.dumps(clean_for_json(op_params)),
            result_summary_json=json.dumps(clean_for_json(summary)),
            status="success"
        )

        # Update dataset latest reference
        dataset.latest_version_id = new_version_id
        dataset.row_count = len(new_df)
        dataset.column_count = len(new_df.columns)

        db.add(new_version)
        db.add(cleaning_op)
        db.commit()
        db.refresh(dataset)
        db.refresh(new_version)
        return new_version

    @staticmethod
    def undo_last_operation(db: Session, dataset_id: str) -> DatasetVersion:
        dataset = DatasetService.get_dataset(db, dataset_id)
        current_version = DatasetService.get_version(db, dataset_id, dataset.latest_version_id)

        if not current_version.parent_version_id:
            raise HTTPException(status_code=400, detail="Cannot undo: Already at the original dataset version.")

        parent_version = db.query(DatasetVersion).filter(
            DatasetVersion.id == current_version.parent_version_id
        ).first()

        if not parent_version:
            raise HTTPException(status_code=404, detail="Parent version not found for undo.")

        # Update dataset latest pointer back to parent
        dataset.latest_version_id = parent_version.id
        
        # Read parent dataframe to restore row/column counts
        parent_df = StorageService.read_dataframe(parent_version.storage_path)
        dataset.row_count = len(parent_df)
        dataset.column_count = len(parent_df.columns)

        # Record undo in operation log
        undo_op = CleaningOperation(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            input_version_id=current_version.id,
            output_version_id=parent_version.id,
            operation_type="undo",
            parameters_json=json.dumps({"restored_version": parent_version.version_number}),
            result_summary_json=json.dumps({"message": f"Restored version {parent_version.version_number}"}),
            status="success"
        )

        db.add(undo_op)
        db.commit()
        db.refresh(dataset)
        return parent_version

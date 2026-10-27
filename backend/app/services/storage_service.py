import os
import shutil
import uuid
import pandas as pd
from fastapi import HTTPException
from app.config import settings

class StorageService:
    @staticmethod
    def get_dataset_dir(dataset_id: str) -> str:
        dataset_dir = os.path.join(settings.STORAGE_DIR, dataset_id)
        os.makedirs(dataset_dir, exist_ok=True)
        return dataset_dir

    @classmethod
    def save_file_stream(cls, dataset_id: str, file_obj, filename: str) -> tuple[str, int]:
        """Save an uploaded file directly into dataset storage directory safely."""
        dataset_dir = cls.get_dataset_dir(dataset_id)
        # Use UUID-based internal filename to avoid any collision or traversal
        ext = os.path.splitext(filename)[1].lower()
        internal_filename = f"v1_raw_{uuid.uuid4().hex[:8]}{ext}"
        target_path = os.path.join(dataset_dir, internal_filename)

        size = 0
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        
        with open(target_path, "wb") as buffer:
            while chunk := file_obj.read(1024 * 1024):  # 1MB chunks
                size += len(chunk)
                if size > max_bytes:
                    buffer.close()
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                    )
                buffer.write(chunk)

        if size == 0:
            if os.path.exists(target_path):
                os.remove(target_path)
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        return target_path, size

    @classmethod
    def read_dataframe(cls, file_path: str) -> pd.DataFrame:
        """Safely read dataframe handling encodings and delimiters."""
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dataset file not found on disk.")
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            # Attempt utf-8, fallback to latin-1
            try:
                # sep=None with python engine auto-detects comma, semicolon, tab
                df = pd.read_csv(file_path, sep=None, engine="python", encoding="utf-8")
            except Exception:
                try:
                    df = pd.read_csv(file_path, sep=None, engine="python", encoding="latin-1")
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
        elif ext == ".xlsx":
            try:
                df = pd.read_excel(file_path, engine="openpyxl")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse Excel file: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

        # Ensure column names are clean strings
        df.columns = [str(c).strip() for c in df.columns]
        return df

    @classmethod
    def save_version_dataframe(cls, dataset_id: str, version_number: int, df: pd.DataFrame) -> str:
        """Save a new version of the dataset as CSV atomically."""
        dataset_dir = cls.get_dataset_dir(dataset_id)
        version_filename = f"v{version_number}_{uuid.uuid4().hex[:8]}.csv"
        target_path = os.path.join(dataset_dir, version_filename)
        temp_path = f"{target_path}.tmp"

        df.to_csv(temp_path, index=False, encoding="utf-8")
        os.replace(temp_path, target_path)
        return target_path

    @classmethod
    def delete_dataset_files(cls, dataset_id: str):
        """Remove dataset directory and all associated versions."""
        dataset_dir = os.path.join(settings.STORAGE_DIR, dataset_id)
        if os.path.exists(dataset_dir):
            shutil.rmtree(dataset_dir, ignore_errors=True)

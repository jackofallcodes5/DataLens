import os
import re
from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
CSV_MIME_TYPES = {"text/csv", "application/vnd.ms-excel", "text/plain", "application/csv"}
XLSX_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream"
}

def sanitize_filename(filename: str) -> str:
    """Sanitize original filename to prevent path traversal or special characters."""
    filename = os.path.basename(filename)
    filename = re.sub(r"[^\w\.\-\_ ]", "_", filename)
    return filename.strip() or "dataset"

def validate_upload_file(file: UploadFile, max_size_bytes: int):
    """Validate uploaded file extension and basic attributes."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty.")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext

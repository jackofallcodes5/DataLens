from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import datetime

# Projects
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

# Datasets
class DatasetResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    original_filename: str
    file_format: str
    file_size: int
    row_count: int
    column_count: int
    latest_version_id: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class DatasetVersionResponse(BaseModel):
    id: str
    dataset_id: str
    version_number: int
    parent_version_id: Optional[str] = None
    operation_type: str
    created_at: datetime.datetime
    metadata_json: Optional[str] = None

    class Config:
        from_attributes = True

class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    version_id: str
    version_number: int
    total_rows: int
    total_columns: int
    columns: List[str]
    rows: List[Dict[str, Any]]
    page: int
    page_size: int

# Cleaning
class CleaningOperationRequest(BaseModel):
    operation_type: str
    parameters: Dict[str, Any]

class CleaningPreviewResponse(BaseModel):
    operation_type: str
    expected_rows: int
    expected_columns: int
    rows_affected: int
    columns_affected: List[str]
    sample_before: List[Dict[str, Any]]
    sample_after: List[Dict[str, Any]]
    warnings: List[str]

class CleaningApplyResponse(BaseModel):
    success: bool
    new_version_id: str
    new_version_number: int
    summary: Dict[str, Any]

class HistoryItemResponse(BaseModel):
    id: str
    operation_type: str
    parameters: Dict[str, Any]
    result_summary: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime.datetime

# Visualization
class ChartDataRequest(BaseModel):
    chart_type: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    aggregation: Optional[str] = "count"
    sort_by: Optional[str] = "none"
    top_n: Optional[int] = 50
    bins: Optional[int] = 10
    title: Optional[str] = ""

class ChartCreateRequest(BaseModel):
    project_id: Optional[str] = None
    dataset_id: str
    dataset_version_id: Optional[str] = None
    title: str
    chart_type: str
    configuration: Dict[str, Any]

class ChartResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    dataset_id: str
    dataset_version_id: Optional[str] = None
    title: str
    chart_type: str
    configuration_json: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

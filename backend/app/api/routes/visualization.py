import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.chart import Chart
from app.services.dataset_service import DatasetService
from app.services.storage_service import StorageService
from app.visualization.chart_service import ChartService
from app.schemas.schemas import ChartDataRequest, ChartCreateRequest, ChartResponse
from app.utils.serialization import clean_for_json

router = APIRouter(tags=["visualization"])

@router.post("/datasets/{dataset_id}/charts/data")
def get_chart_data(
    dataset_id: str,
    req: ChartDataRequest,
    version_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    version = DatasetService.get_version(db, dataset_id, version_id)
    df = StorageService.read_dataframe(version.storage_path)
    data = ChartService.generate_chart_data(df, req.model_dump())
    return clean_for_json(data)

@router.get("/datasets/{dataset_id}/charts/recommendations")
def get_recommendations(
    dataset_id: str,
    version_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    version = DatasetService.get_version(db, dataset_id, version_id)
    df = StorageService.read_dataframe(version.storage_path)
    recs = ChartService.get_recommendations(df)
    return clean_for_json(recs)

@router.get("/charts", response_model=List[ChartResponse])
def list_charts(
    dataset_id: Optional[str] = None,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Chart)
    if dataset_id:
        query = query.filter(Chart.dataset_id == dataset_id)
    if project_id:
        query = query.filter(Chart.project_id == project_id)
    return query.order_by(Chart.created_at.desc()).all()

@router.post("/charts", response_model=ChartResponse, status_code=201)
def save_chart(req: ChartCreateRequest, db: Session = Depends(get_db)):
    # Verify dataset exists
    dataset = DatasetService.get_dataset(db, req.dataset_id)
    chart = Chart(
        id=str(uuid.uuid4()),
        project_id=req.project_id or dataset.project_id,
        dataset_id=req.dataset_id,
        dataset_version_id=req.dataset_version_id or dataset.latest_version_id,
        title=req.title.strip(),
        chart_type=req.chart_type,
        configuration_json=json.dumps(req.configuration)
    )
    db.add(chart)
    db.commit()
    db.refresh(chart)
    return chart

@router.get("/charts/{chart_id}", response_model=ChartResponse)
def get_chart(chart_id: str, db: Session = Depends(get_db)):
    chart = db.query(Chart).filter(Chart.id == chart_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found.")
    return chart

@router.delete("/charts/{chart_id}")
def delete_chart(chart_id: str, db: Session = Depends(get_db)):
    chart = db.query(Chart).filter(Chart.id == chart_id).first()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found.")
    db.delete(chart)
    db.commit()
    return {"status": "success", "message": f"Chart '{chart_id}' deleted."}

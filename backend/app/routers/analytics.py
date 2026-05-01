from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from ..database import get_db
from ..services.dataset import DatasetService
from ..models.dataset import Dataset

router = APIRouter()

@router.get('/summary/{dataset_id}')
def dataset_summary(dataset_id: int, db: Session = Depends(get_db)):
    dataset = DatasetService.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found')
    return {'metadata': dataset.metadata_json or {}, 'rows': dataset.row_count, 'columns': dataset.column_count}

@router.get('/correlation/{dataset_id}')
def correlation_matrix(dataset_id: int, db: Session = Depends(get_db)):
    dataset = DatasetService.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found')
    df = DatasetService.load_dataset(dataset)
    correlation = df.select_dtypes(include=['number']).corr().fillna(0).to_dict()
    return {'correlation': correlation}

@router.get('/distribution/{dataset_id}')
def distribution(dataset_id: int, db: Session = Depends(get_db)):
    dataset = DatasetService.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found')
    df = DatasetService.load_dataset(dataset)
    summary = {col: df[col].value_counts().head(10).to_dict() for col in df.select_dtypes(include=['object', 'category']).columns}
    return {'distributions': summary}

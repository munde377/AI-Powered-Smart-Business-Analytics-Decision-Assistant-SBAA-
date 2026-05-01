"""Machine Learning API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import logging
import os

from celery.result import AsyncResult
from ..database import get_db
from ..services.ml_pipeline import MLPipeline
from ..services.monitoring import MonitoringService
from ..core.security import get_current_active_user
from ..models.user import User
from ..models.model_meta import ModelMeta
from ..tasks.workers import train_ml_model

logger = logging.getLogger(__name__)
router = APIRouter()

class TrainMLRequest(BaseModel):
    """Request for training ML model."""
    dataset_id: int
    target_column: str
    feature_columns: Optional[list[str]] = None
    model_name: str
    model_type: str = Field(..., description="'regression' or 'classification'")
    algorithm: str = Field('randomforest', description="'randomforest', 'linear', or 'logistic'")

class PredictMLRequest(BaseModel):
    """Request for prediction."""
    model_id: int
    record: dict

class PredictMLResponse(BaseModel):
    """Response from prediction."""
    prediction: float | int
    confidence: Optional[float] = None
    model_name: str
    model_type: str

class ModelStatusResponse(BaseModel):
    """Model status and metrics."""
    id: int
    name: str
    model_type: str
    algorithm: str
    status: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    rmse: Optional[float] = None
    training_samples: Optional[int] = None
    test_samples: Optional[int] = None
    training_time_seconds: Optional[float] = None

class ModelMetaRead(BaseModel):
    """Model metadata response."""
    id: int
    name: str
    model_type: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    created_at: str
    
    class Config:
        orm_mode = True

@router.post('/train')
def train_model(
    request: TrainMLRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Train a machine learning model asynchronously using Celery."""
    try:
        # Submit training task to Celery
        task = train_ml_model.delay(
            user_id=current_user.id,
            dataset_id=request.dataset_id,
            target_column=request.target_column,
            model_type=request.model_type,
            algorithm=request.algorithm,
            model_name=request.model_name
        )

        logger.info(f'User {current_user.id} submitted ML training task: {task.id}')

        return {
            'message': 'Model training started',
            'task_id': task.id,
            'status': 'pending'
        }

    except Exception as e:
        logger.error(f'Model training task submission failed: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Model training failed: {str(e)}'
        )

@router.get('/task/{task_id}')
def get_task_status(task_id: str):
    """Get Celery task status."""
    result = AsyncResult(task_id)
    return {
        'task_id': task_id,
        'status': result.status,
        'result': result.result
    }

@router.post('/predict', response_model=PredictMLResponse)
def predict(
    request: PredictMLRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Make prediction using trained model."""
    try:
        result = MLPipeline.predict(db, request.model_id, request.record)
        model_meta = result['model_meta']
        
        MonitoringService.log_prediction(
            db,
            user_id=current_user.id,
            model_id=request.model_id,
            dataset_id=model_meta.dataset_id,
            record=request.record,
            prediction={
                'prediction': result['prediction'],
                'confidence': result.get('confidence')
            },
            comment='ML prediction'
        )

        logger.info(f'User {current_user.id} made prediction with model {request.model_id}')

        return PredictMLResponse(
            prediction=result['prediction'],
            confidence=result.get('confidence'),
            model_name=model_meta.name,
            model_type=model_meta.model_type
        )
    
    except Exception as e:
        logger.error(f'Prediction failed: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Prediction failed: {str(e)}'
        )

@router.get('/model-status/{model_id}', response_model=ModelStatusResponse)
def get_model_status(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get model status and performance metrics."""
    try:
        status_info = MLPipeline.get_model_status(db, model_id)
        return ModelStatusResponse(**status_info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Model not found: {str(e)}'
        )

@router.get('/models', response_model=list[ModelMetaRead])
def list_models(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's trained models."""
    query = db.query(ModelMeta).filter(ModelMeta.user_id == current_user.id)
    return query.offset(skip).limit(limit).all()

@router.delete('/models/{model_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete trained model."""
    model = db.query(ModelMeta).filter(
        ModelMeta.id == model_id,
        ModelMeta.user_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Model not found'
        )
    
    try:
        if os.path.exists(model.model_path):
            os.remove(model.model_path)
    except Exception as e:
        logger.warning(f'Could not delete model file: {str(e)}')
    
    db.delete(model)
    db.commit()
    logger.info(f'User {current_user.id} deleted model {model_id}')

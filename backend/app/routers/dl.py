"""Deep Learning API endpoints for LSTM forecasting."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import os

from ..database import get_db
from ..services.dl_pipeline import DLPipeline
from ..services.monitoring import MonitoringService
from ..core.security import get_current_active_user
from ..models.user import User
from ..models.model_meta import ModelMeta
from ..tasks.workers import train_lstm_model

logger = logging.getLogger(__name__)
router = APIRouter()

class TrainLSTMRequest(BaseModel):
    """Request for training LSTM model."""
    dataset_id: int
    target_column: str
    lookback_steps: int = Field(12, description="Number of past timesteps to use for prediction")
    forecast_steps: int = Field(7, description="Number of future steps to forecast")

class PredictLSTMRequest(BaseModel):
    """Request for LSTM prediction."""
    model_id: int
    history: List[float] = Field(..., description="Historical values for forecasting")
    forecast_steps: int = Field(7, description="Number of steps to forecast")

class LSTMResponse(BaseModel):
    """Response from LSTM operations."""
    model_id: int
    predictions: Optional[List[float]] = None
    accuracy: Optional[float] = None
    training_time_seconds: Optional[float] = None

class ModelMetaRead(BaseModel):
    """Model metadata response."""
    id: int
    name: str
    model_type: str
    accuracy: Optional[float] = None
    rmse: Optional[float] = None
    created_at: str
    
    class Config:
        orm_mode = True

@router.post('/train-lstm')
def train_lstm(
    request: TrainLSTMRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Train LSTM model asynchronously using Celery."""
    try:
        # Submit training task to Celery
        task = train_lstm_model.delay(
            user_id=current_user.id,
            dataset_id=request.dataset_id,
            target_column=request.target_column,
            lookback_steps=request.lookback_steps,
            forecast_steps=request.forecast_steps
        )

        logger.info(f'User {current_user.id} submitted LSTM training task: {task.id}')

        return {
            'message': 'LSTM training started',
            'task_id': task.id,
            'status': 'pending'
        }

    except Exception as e:
        logger.error(f'LSTM training task submission failed: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'LSTM training failed: {str(e)}'
        )

@router.post('/predict-lstm', response_model=LSTMResponse)
def predict_lstm(
    request: PredictLSTMRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Make LSTM predictions."""
    try:
        result = DLPipeline.predict_lstm(
            db=db,
            model_id=request.model_id,
            history=request.history,
            forecast_steps=request.forecast_steps
        )
        
        model_meta = result['model_meta']
        
        MonitoringService.log_prediction(
            db,
            user_id=current_user.id,
            model_id=request.model_id,
            dataset_id=model_meta.dataset_id,
            record={'history_length': len(request.history), 'forecast_steps': request.forecast_steps},
            prediction={'predictions': result['predictions']},
            comment='LSTM forecast'
        )
        
        logger.info(f'User {current_user.id} made LSTM prediction with model {request.model_id}')
        
        return LSTMResponse(
            model_id=model_meta.id,
            predictions=result['predictions'],
            accuracy=model_meta.accuracy,
            training_time_seconds=model_meta.training_time_seconds
        )
    
    except Exception as e:
        logger.error(f'LSTM prediction failed: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'LSTM prediction failed: {str(e)}'
        )

@router.get('/lstm-models', response_model=list[ModelMetaRead])
def list_lstm_models(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's trained LSTM models."""
    query = db.query(ModelMeta).filter(
        ModelMeta.user_id == current_user.id,
        ModelMeta.model_type == 'lstm'
    )
    return query.offset(skip).limit(limit).all()

@router.delete('/lstm-models/{model_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_lstm_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete trained LSTM model."""
    model = db.query(ModelMeta).filter(
        ModelMeta.id == model_id,
        ModelMeta.user_id == current_user.id,
        ModelMeta.model_type == 'lstm'
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='LSTM model not found'
        )
    
    try:
        if os.path.exists(model.model_path):
            os.remove(model.model_path)
        # Also remove scaler if exists
        scaler_path = model.params.get('scaler_path')
        if scaler_path and os.path.exists(scaler_path):
            os.remove(scaler_path)
    except Exception as e:
        logger.warning(f'Could not delete LSTM model files: {str(e)}')
    
    db.delete(model)
    db.commit()
    logger.info(f'User {current_user.id} deleted LSTM model {model_id}')

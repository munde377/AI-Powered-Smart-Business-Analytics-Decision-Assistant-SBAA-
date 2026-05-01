from .celery_app import celery
from ..services.dataset import DatasetService
from ..services.ml_pipeline import MLTrainingService
from ..services.dl_pipeline import DLTrainingService
from ..services.alerts import AlertService
from ..database import SessionLocal
from ..models import Dataset, ModelMeta, AlertRule
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@celery.task(name='backend.app.tasks.workers.process_dataset', bind=True)
def process_dataset(self, dataset_id: int):
    """Background task for dataset ingestion and cleaning."""
    db = SessionLocal()
    try:
        DatasetService.process_dataset_file(db, dataset_id)
        return {'dataset_id': dataset_id, 'status': 'completed'}
    except Exception as e:
        logger.error(f"Dataset processing failed for ID {dataset_id}: {str(e)}")
        return {'dataset_id': dataset_id, 'status': 'failed', 'error': str(e)}
    finally:
        db.close()

@celery.task(name='backend.app.tasks.workers.train_ml_model', bind=True)
def train_ml_model(self, user_id: int, dataset_id: int, target_column: str,
                   model_type: str, algorithm: str, model_name: str):
    """Background task for ML model training."""
    db = SessionLocal()
    try:
        service = MLTrainingService()
        result = service.train_model(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
            target_column=target_column,
            model_type=model_type,
            algorithm=algorithm,
            model_name=model_name
        )
        return {'model_id': result.id, 'status': 'completed', 'accuracy': result.accuracy}
    except Exception as e:
        logger.error(f"ML training failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}
    finally:
        db.close()

@celery.task(name='backend.app.tasks.workers.train_lstm_model', bind=True)
def train_lstm_model(self, user_id: int, dataset_id: int, target_column: str,
                     lookback_steps: int, forecast_steps: int):
    """Background task for LSTM model training."""
    db = SessionLocal()
    try:
        service = DLTrainingService()
        result = service.train_lstm(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
            target_column=target_column,
            lookback_steps=lookback_steps,
            forecast_steps=forecast_steps
        )
        return {'model_id': result.id, 'status': 'completed', 'accuracy': result.accuracy}
    except Exception as e:
        logger.error(f"LSTM training failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}
    finally:
        db.close()

@celery.task(name='backend.app.tasks.workers.evaluate_alerts', bind=True)
def evaluate_alerts(self):
    """Background task to evaluate all active alert rules."""
    db = SessionLocal()
    try:
        alert_service = AlertService()
        triggered_alerts = alert_service.evaluate_all_alerts(db)

        results = []
        for alert in triggered_alerts:
            results.append({
                'alert_id': alert.id,
                'type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message
            })

        return {'status': 'completed', 'alerts_triggered': len(results), 'alerts': results}
    except Exception as e:
        logger.error(f"Alert evaluation failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}
    finally:
        db.close()

@celery.task(name='backend.app.tasks.workers.check_sales_drop_alerts', bind=True)
def check_sales_drop_alerts(self):
    """Check for sales drop alerts across all datasets."""
    db = SessionLocal()
    try:
        alert_service = AlertService()
        alerts = alert_service.check_sales_drop_alerts(db)
        return {'status': 'completed', 'alerts_created': len(alerts)}
    except Exception as e:
        logger.error(f"Sales drop alert check failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}
    finally:
        db.close()

@celery.task(name='backend.app.tasks.workers.check_anomaly_alerts', bind=True)
def check_anomaly_alerts(self):
    """Check for anomaly detection alerts."""
    db = SessionLocal()
    try:
        alert_service = AlertService()
        alerts = alert_service.check_anomaly_alerts(db)
        return {'status': 'completed', 'alerts_created': len(alerts)}
    except Exception as e:
        logger.error(f"Anomaly alert check failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}
    finally:
        db.close()

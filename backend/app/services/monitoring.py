from numbers import Number
from sqlalchemy.orm import Session
from ..models.dataset import Dataset
from ..models.model_meta import ModelMeta
from ..models.alert import Alert
from ..models.log import PredictionLog

class MonitoringService:
    @staticmethod
    def log_prediction(
        db: Session,
        user_id: int | None,
        model_id: int | None,
        dataset_id: int | None,
        record: dict,
        prediction: dict,
        comment: str | None = None,
        status: str = 'success'
    ) -> PredictionLog:
        prediction_value = None
        confidence_score = None

        if 'prediction' in prediction:
            value = prediction['prediction']
            if isinstance(value, Number):
                prediction_value = float(value)
            elif isinstance(value, list) and value:
                first_value = value[0]
                if isinstance(first_value, Number):
                    prediction_value = float(first_value)
        elif 'predictions' in prediction and isinstance(prediction['predictions'], list) and prediction['predictions']:
            first_value = prediction['predictions'][0]
            if isinstance(first_value, Number):
                prediction_value = float(first_value)

        if 'confidence' in prediction and isinstance(prediction['confidence'], Number):
            confidence_score = float(prediction['confidence'])
        elif 'confidence_score' in prediction and isinstance(prediction['confidence_score'], Number):
            confidence_score = float(prediction['confidence_score'])

        log = PredictionLog(
            user_id=user_id,
            model_id=model_id,
            dataset_id=dataset_id,
            input_data=record,
            output_data=prediction,
            prediction_value=prediction_value,
            confidence_score=confidence_score,
            comment=comment,
            status=status
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_kpis(db: Session) -> dict[str, int | float]:
        dataset_count = db.query(Dataset).count()
        model_count = db.query(ModelMeta).count()
        active_alerts = db.query(Alert).filter(Alert.status == 'active').count()
        return {
            'dataset_count': dataset_count,
            'model_count': model_count,
            'active_alerts': active_alerts,
        }

    @staticmethod
    def list_logs(db: Session, skip: int = 0, limit: int = 20):
        return db.query(PredictionLog).offset(skip).limit(limit).all()

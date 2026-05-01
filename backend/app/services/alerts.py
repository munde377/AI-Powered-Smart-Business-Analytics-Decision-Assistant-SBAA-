from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from ..models.alert import AlertRule, Alert
from ..models.dataset import Dataset
from ..models.model_meta import ModelMeta
from ..models.log import PredictionLog
from ..database import SessionLocal
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AlertService:
    @staticmethod
    def create_alert_rule(db: Session, name: str, description: str, alert_type: str,
                         metric: str, condition: str, threshold: float,
                         cooldown_minutes: int = 60) -> AlertRule:
        """Create a new alert rule."""
        rule = AlertRule(
            name=name,
            description=description,
            alert_type=alert_type,
            metric=metric,
            condition=condition,
            threshold=threshold,
            cooldown_minutes=cooldown_minutes,
            active=True
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def list_alert_rules(db: Session, skip: int = 0, limit: int = 20):
        """List all alert rules."""
        return db.query(AlertRule).offset(skip).limit(limit).all()

    @staticmethod
    def list_alerts(db: Session, user_id: int = None, status: str = None,
                   skip: int = 0, limit: int = 20):
        """List alerts with optional filtering."""
        query = db.query(Alert)
        if user_id:
            query = query.filter(Alert.user_id == user_id)
        if status:
            query = query.filter(Alert.status == status)
        return query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int, user_id: int) -> bool:
        """Acknowledge an alert."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert and alert.user_id == user_id:
            alert.status = 'acknowledged'
            alert.acknowledged_at = datetime.utcnow()
            db.commit()
            return True
        return False

    @staticmethod
    def resolve_alert(db: Session, alert_id: int, user_id: int) -> bool:
        """Resolve an alert."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert and alert.user_id == user_id:
            alert.status = 'resolved'
            alert.resolved_at = datetime.utcnow()
            db.commit()
            return True
        return False

    @staticmethod
    def evaluate_all_alerts(db: Session) -> List[Alert]:
        """Evaluate all active alert rules and create alerts if triggered."""
        rules = db.query(AlertRule).filter(AlertRule.active == True).all()
        triggered_alerts = []

        for rule in rules:
            alerts = AlertService._evaluate_rule(db, rule)
            triggered_alerts.extend(alerts)

        return triggered_alerts

    @staticmethod
    def _evaluate_rule(db: Session, rule: AlertRule) -> List[Alert]:
        """Evaluate a single alert rule."""
        alerts = []

        if rule.alert_type == 'sales_drop':
            alerts.extend(AlertService._check_sales_drop(db, rule))
        elif rule.alert_type == 'high_demand':
            alerts.extend(AlertService._check_high_demand(db, rule))
        elif rule.alert_type == 'model_drift':
            alerts.extend(AlertService._check_model_drift(db, rule))
        elif rule.alert_type == 'anomaly_detection':
            alerts.extend(AlertService._check_anomalies(db, rule))

        return alerts

    @staticmethod
    def check_sales_drop_alerts(db: Session) -> List[Alert]:
        """Check for sales drop alerts across all datasets."""
        alerts = []
        rules = db.query(AlertRule).filter(
            and_(AlertRule.active == True, AlertRule.alert_type == 'sales_drop')
        ).all()

        for rule in rules:
            alerts.extend(AlertService._check_sales_drop(db, rule))

        return alerts

    @staticmethod
    def _check_sales_drop(db: Session, rule: AlertRule) -> List[Alert]:
        """Check for sales drop based on recent predictions."""
        alerts = []

        # Get recent predictions for sales-related models
        recent_predictions = db.query(PredictionLog).filter(
            and_(
                PredictionLog.created_at >= datetime.utcnow() - timedelta(hours=24),
                PredictionLog.status == 'success'
            )
        ).all()

        for pred in recent_predictions:
            if pred.prediction_value and pred.prediction_value < rule.threshold:
                # Check if similar alert was created recently (cooldown)
                recent_alert = db.query(Alert).filter(
                    and_(
                        Alert.alert_type == 'sales_drop',
                        Alert.dataset_id == pred.dataset_id,
                        Alert.created_at >= datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)
                    )
                ).first()

                if not recent_alert:
                    alert = Alert(
                        user_id=pred.user_id,
                        alert_rule_id=rule.id,
                        alert_type='sales_drop',
                        severity='high',
                        title='Sales Drop Alert',
                        message=f'Sales dropped to {pred.prediction_value:.2f}, below threshold of {rule.threshold}',
                        metric_value=pred.prediction_value,
                        threshold_value=rule.threshold,
                        dataset_id=pred.dataset_id,
                        model_id=pred.model_id,
                        status='active'
                    )
                    db.add(alert)
                    alerts.append(alert)

        db.commit()
        return alerts

    @staticmethod
    def check_anomaly_alerts(db: Session) -> List[Alert]:
        """Check for anomaly detection alerts."""
        alerts = []
        rules = db.query(AlertRule).filter(
            and_(AlertRule.active == True, AlertRule.alert_type == 'anomaly_detection')
        ).all()

        for rule in rules:
            alerts.extend(AlertService._check_anomalies(db, rule))

        return alerts

    @staticmethod
    def _check_anomalies(db: Session, rule: AlertRule) -> List[Alert]:
        """Check for anomalies in prediction patterns."""
        alerts = []

        # Get recent predictions for analysis
        recent_predictions = db.query(PredictionLog).filter(
            and_(
                PredictionLog.created_at >= datetime.utcnow() - timedelta(hours=24),
                PredictionLog.status == 'success',
                PredictionLog.prediction_value.isnot(None)
            )
        ).order_by(PredictionLog.created_at).all()

        if len(recent_predictions) < 10:  # Need minimum data for anomaly detection
            return alerts

        # Simple anomaly detection using z-score
        values = [p.prediction_value for p in recent_predictions]
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:  # No variation
            return alerts

        # Check last few predictions for anomalies
        recent_values = values[-5:]  # Last 5 predictions

        for i, value in enumerate(recent_values):
            z_score = abs((value - mean) / std)
            if z_score > rule.threshold:  # threshold is z-score threshold
                pred = recent_predictions[len(values) - 5 + i]

                # Check cooldown
                recent_alert = db.query(Alert).filter(
                    and_(
                        Alert.alert_type == 'anomaly_detection',
                        Alert.dataset_id == pred.dataset_id,
                        Alert.created_at >= datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)
                    )
                ).first()

                if not recent_alert:
                    alert = Alert(
                        user_id=pred.user_id,
                        alert_rule_id=rule.id,
                        alert_type='anomaly_detection',
                        severity='medium',
                        title='Anomaly Detected',
                        message=f'Anomalous value detected: {value:.2f} (z-score: {z_score:.2f})',
                        metric_value=value,
                        threshold_value=rule.threshold,
                        dataset_id=pred.dataset_id,
                        model_id=pred.model_id,
                        status='active',
                        metadata={'z_score': z_score, 'mean': mean, 'std': std}
                    )
                    db.add(alert)
                    alerts.append(alert)

        db.commit()
        return alerts

    @staticmethod
    def _check_high_demand(db: Session, rule: AlertRule) -> List[Alert]:
        """Check for high demand patterns."""
        # Implementation for high demand alerts
        return []

    @staticmethod
    def _check_model_drift(db: Session, rule: AlertRule) -> List[Alert]:
        """Check for model performance drift."""
        # Implementation for model drift alerts
        return []

    @staticmethod
    def create_default_alert_rules(db: Session):
        """Create default alert rules for the system."""
        default_rules = [
            {
                'name': 'Sales Drop Alert',
                'description': 'Alert when sales drop below threshold',
                'alert_type': 'sales_drop',
                'metric': 'sales_value',
                'condition': 'less_than',
                'threshold': 50000.0,
                'cooldown_minutes': 60
            },
            {
                'name': 'Anomaly Detection',
                'description': 'Detect anomalous prediction values',
                'alert_type': 'anomaly_detection',
                'metric': 'prediction_value',
                'condition': 'z_score_greater_than',
                'threshold': 3.0,  # 3 standard deviations
                'cooldown_minutes': 120
            }
        ]

        for rule_data in default_rules:
            existing = db.query(AlertRule).filter(AlertRule.name == rule_data['name']).first()
            if not existing:
                AlertService.create_alert_rule(db, **rule_data)

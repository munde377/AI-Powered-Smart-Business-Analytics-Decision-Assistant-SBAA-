from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from ..database import get_db
from ..services.alerts import AlertService
from ..core.security import get_current_active_user
from ..models.user import User

router = APIRouter()

class AlertRuleRead(BaseModel):
    id: int
    name: str
    description: str | None
    alert_type: str
    metric: str
    condition: str
    threshold: float
    cooldown_minutes: int
    active: bool
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True

class AlertRead(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    metric_value: float | None
    threshold_value: float | None
    dataset_id: int | None
    model_id: int | None
    status: str
    acknowledged_at: str | None
    resolved_at: str | None
    metadata: dict | None
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True

@router.post('/rules', response_model=AlertRuleRead, status_code=status.HTTP_201_CREATED)
def create_alert_rule(
    name: str,
    description: str,
    alert_type: str,
    metric: str,
    condition: str,
    threshold: float,
    cooldown_minutes: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return AlertService.create_alert_rule(
        db, name, description, alert_type, metric, condition, threshold, cooldown_minutes
    )

@router.get('/rules', response_model=List[AlertRuleRead])
def list_alert_rules(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return AlertService.list_alert_rules(db, skip=skip, limit=limit)

@router.get('/', response_model=List[AlertRead])
def list_alerts(
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return AlertService.list_alerts(db, user_id=current_user.id, status=status, skip=skip, limit=limit)

@router.post('/{alert_id}/acknowledge')
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    success = AlertService.acknowledge_alert(db, alert_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Alert not found or not authorized')
    return {'message': 'Alert acknowledged'}

@router.post('/{alert_id}/resolve')
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    success = AlertService.resolve_alert(db, alert_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Alert not found or not authorized')
    return {'message': 'Alert resolved'}

@router.post('/evaluate')
def evaluate_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    alerts = AlertService.evaluate_all_alerts(db)
    return {'alerts_triggered': len(alerts), 'alerts': alerts}

@router.post('/check-sales-drop')
def check_sales_drop_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    alerts = AlertService.check_sales_drop_alerts(db)
    return {'alerts_created': len(alerts), 'alerts': alerts}

@router.post('/check-anomalies')
def check_anomaly_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    alerts = AlertService.check_anomaly_alerts(db)
    return {'alerts_created': len(alerts), 'alerts': alerts}

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.monitoring import MonitoringService
from ..core.security import get_current_active_user
from ..models.user import User
from ..schemas.log import PredictionLogRead

router = APIRouter()

@router.get('/kpis')
def get_kpis(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return MonitoringService.get_kpis(db)

@router.get('/logs', response_model=list[PredictionLogRead])
def get_logs(skip: int = 0, limit: int = 20, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return MonitoringService.list_logs(db, skip=skip, limit=limit)

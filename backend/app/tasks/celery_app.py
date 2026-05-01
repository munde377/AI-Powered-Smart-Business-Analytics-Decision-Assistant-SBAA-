from celery import Celery
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app with environment-aware broker/backend configuration
celery = Celery(
    'smart_analytics',
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Celery configuration
celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    result_expires=3600,  # 1 hour
)

# Task routing
celery.conf.task_routes = {
    'backend.app.tasks.workers.*': {'queue': 'analytics_queue'}
}

logger.info(f'Celery configured with broker: {settings.redis_url}')
logger.info(f'Celery configured with result_backend: {settings.redis_url}')

# Import tasks and beat schedule to ensure Celery discovers them when worker or beat starts
from . import workers  # noqa: E402, F401
from . import celery_beat  # noqa: E402, F401

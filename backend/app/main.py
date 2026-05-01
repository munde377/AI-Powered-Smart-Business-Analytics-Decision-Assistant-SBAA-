import time
import logging
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from redis import Redis, RedisError
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from .database import engine, Base, SessionLocal
from .routers import auth, upload, analytics, ml, dl, genai, dashboard, alerts
from .models import user, dataset, model_meta, alert, log, chat, api_log
from .config import settings
from .core.exceptions import api_error_handler, request_validation_exception_handler, general_exception_handler, APIError
from .core.middleware import APILoggingMiddleware, RequestValidationMiddleware
from .services.alerts import AlertService

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title='AI-Powered Smart Business Analytics & Decision Assistant',
    version='1.0.0',
    description='Enterprise-level business analytics and decision assistant platform with ML/DL and GenAI integration.',
    debug=settings.debug
)

# Mount frontend static build output when available
STATIC_DIR = Path(__file__).resolve().parent / 'static'
INDEX_FILE = STATIC_DIR / 'index.html'
if STATIC_DIR.exists():
    app.mount('/assets', StaticFiles(directory=str(STATIC_DIR / 'assets')), name='static_assets')

# Custom middleware
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(APILoggingMiddleware)

# Exception handlers
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router, prefix='/api/auth', tags=['auth'])
app.include_router(upload.router, prefix='/api/data', tags=['data'])
app.include_router(analytics.router, prefix='/api/analytics', tags=['analytics'])
app.include_router(ml.router, prefix='/api/ml', tags=['ml'])
app.include_router(dl.router, prefix='/api/dl', tags=['dl'])
app.include_router(genai.router, prefix='/api/genai', tags=['genai'])
app.include_router(dashboard.router, prefix='/api/dashboard', tags=['dashboard'])
app.include_router(alerts.router, prefix='/api/alerts', tags=['alerts'])

@app.get('/api/status')
def api_status():
    """Basic API status endpoint."""
    return {
        'status': 'ok',
        'message': 'Smart Business Analytics API is running',
        'version': '1.0.0',
        'environment': settings.environment
    }

def check_redis_connection() -> str:
    """Check Redis connectivity using settings.REDIS_URL."""
    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        return 'connected'
    except RedisError as exc:
        logger.warning(f'Redis health check failed: {exc}')
        return 'disconnected'

@app.get('/api/health')
def health_check():
    """Comprehensive health check with dependency status."""
    health_data = {
        'status': 'healthy',
        'version': '1.0.0',
        'environment': settings.environment,
        'services': {}
    }

    # Check database
    try:
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        health_data['services']['database'] = 'connected'
    except Exception as exc:
        health_data['services']['database'] = 'disconnected'
        health_data['status'] = 'degraded'

    # Check Redis
    redis_status = check_redis_connection()
    health_data['services']['redis'] = redis_status
    if redis_status != 'connected':
        health_data['status'] = 'degraded'

    logger.debug(f'Health check: {health_data["status"]}')
    return health_data

@app.get('/{path_name:path}')
async def spa_fallback(request: Request, path_name: str):
    """Serve the React single-page application for all non-API routes."""
    if path_name.startswith('api') or path_name.startswith('assets'):
        raise HTTPException(status_code=404, detail='API route not found')

    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)

    raise HTTPException(status_code=404, detail='Frontend build not found')

@app.on_event('startup')
def startup_event():
    """Validate service dependencies and initialize system."""
    logger.info(f'Starting application in {settings.environment} mode (debug={settings.debug})')
    
    # Try to connect to database
    max_attempts = 12
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text('SELECT 1'))
            logger.info('✓ Database connection established')
            break
        except OperationalError as exc:
            logger.warning(f'Database unavailable on startup attempt {attempt}/{max_attempts}: {exc}')
            if attempt == max_attempts:
                logger.error('✗ Failed to connect to database after 12 attempts')
                raise RuntimeError('Unable to connect to database during startup')
            time.sleep(5)

    # Try to connect to Redis
    if settings.is_production:
        for attempt in range(1, max_attempts + 1):
            try:
                redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
                redis_client.ping()
                logger.info('✓ Redis connection established')
                break
            except RedisError as exc:
                logger.warning(f'Redis unavailable on startup attempt {attempt}/{max_attempts}: {exc}')
                if attempt == max_attempts:
                    logger.error('✗ Failed to connect to Redis after 12 attempts')
                    raise RuntimeError('Unable to connect to Redis during startup')
                time.sleep(5)
    else:
        try:
            redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
            redis_client.ping()
            logger.info('✓ Redis connection established')
        except RedisError as exc:
            logger.warning(f'Non-production startup: Redis unavailable, continuing without Redis: {exc}')

    # Initialize database
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info('✓ Database schema initialized')
    except Exception as exc:
        logger.error(f'Failed to initialize database schema: {exc}')
        raise

    # Initialize default alert rules
    try:
        with SessionLocal() as db:
            AlertService.create_default_alert_rules(db)
        logger.info('✓ Default alert rules initialized')
    except Exception as exc:
        logger.error(f'Failed to initialize alert rules: {exc}')
        raise

    logger.info('✓ Application startup complete')

@app.on_event('shutdown')
def shutdown_event():
    """Cleanup on shutdown."""
    logger.info('Application shutting down')

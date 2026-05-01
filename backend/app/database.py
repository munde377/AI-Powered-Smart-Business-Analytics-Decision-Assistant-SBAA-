from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool, NullPool
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Create engine with production-appropriate pool settings
if settings.is_production:
    # Use QueuePool for production with connection pooling
    engine = create_engine(
        settings.database_url,
        future=True,
        echo=settings.db_echo,
        pool_pre_ping=True,
        poolclass=QueuePool,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
        connect_args={'connect_timeout': 10}
    )
else:
    # Use NullPool for development (no connection pooling)
    engine = create_engine(
        settings.database_url,
        future=True,
        echo=settings.db_echo,
        pool_pre_ping=True,
        poolclass=NullPool
    )

# Add event listeners for better error handling
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Set connection-level options for PostgreSQL."""
    if 'postgresql' in settings.database_url.lower():
        cursor = dbapi_conn.cursor()
        cursor.execute("SET SESSION AUTOCOMMIT=OFF")
        cursor.close()

@event.listens_for(engine, "engine_disposed")
def receive_engine_disposed(engine):
    logger.warning("Database engine was disposed")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

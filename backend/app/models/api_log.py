from sqlalchemy import Column, Integer, String, DateTime, Float, Index, Text
from sqlalchemy.sql import func
from ..database import Base

class APILog(Base):
    """API request/response logging for monitoring and debugging."""
    __tablename__ = 'api_logs'

    id = Column(Integer, primary_key=True, index=True)
    
    # Request details
    method = Column(String(10), nullable=False)
    endpoint = Column(String(512), nullable=False)
    status_code = Column(Integer, nullable=True)
    
    # User info
    user_id = Column(Integer, nullable=True)
    
    # Performance
    response_time_ms = Column(Float, nullable=True)
    
    # Additional info
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_api_log_user_id', 'user_id'),
        Index('idx_api_log_endpoint', 'endpoint'),
        Index('idx_api_log_created_at', 'created_at'),
    )

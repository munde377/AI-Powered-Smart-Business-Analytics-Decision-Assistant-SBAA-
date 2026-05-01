from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Index, Text
from sqlalchemy.sql import func
from ..database import Base

class PredictionLog(Base):
    """Log for all predictions made by models."""
    __tablename__ = 'prediction_logs'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    model_id = Column(Integer, ForeignKey('model_meta.id', ondelete='SET NULL'), nullable=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id', ondelete='SET NULL'), nullable=True)
    
    # Input/Output data
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    # Prediction details
    prediction_value = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Metadata
    comment = Column(Text, nullable=True)
    status = Column(String(50), default='success', nullable=False)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_prediction_user_id', 'user_id'),
        Index('idx_prediction_model_id', 'model_id'),
        Index('idx_prediction_dataset_id', 'dataset_id'),
        Index('idx_prediction_created_at', 'created_at'),
    )

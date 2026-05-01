from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Index, Text
from sqlalchemy.sql import func
from ..database import Base

class ModelMeta(Base):
    """Model metadata for tracking trained ML/DL models."""
    __tablename__ = 'model_meta'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    dataset_id = Column(Integer, ForeignKey('datasets.id', ondelete='SET NULL'), nullable=True)
    
    name = Column(String(255), nullable=False)
    model_type = Column(String(100), nullable=False)  # 'regression', 'classification', 'lstm', etc.
    algorithm = Column(String(100), nullable=True)  # 'linear', 'randomforest', 'lstm', etc.
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    
    # Model storage
    model_path = Column(String(512), nullable=False)
    
    # Configuration
    params = Column(JSON, nullable=True)  # Hyperparameters
    feature_names = Column(JSON, nullable=True)
    target_column = Column(String(255), nullable=True)
    
    # Training info
    training_samples = Column(Integer, nullable=True)
    test_samples = Column(Integer, nullable=True)
    training_time_seconds = Column(Float, nullable=True)
    
    status = Column(String(50), default='trained', nullable=False)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_model_user_id', 'user_id'),
        Index('idx_model_dataset_id', 'dataset_id'),
        Index('idx_model_type', 'model_type'),
    )

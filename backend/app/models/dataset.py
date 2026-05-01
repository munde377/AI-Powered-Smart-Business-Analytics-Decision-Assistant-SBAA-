from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Float, Index
from sqlalchemy.sql import func
from ..database import Base

class Dataset(Base):
    """Dataset model for uploaded files and metadata."""
    __tablename__ = 'datasets'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    
    # Data statistics
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    columns_list = Column(JSON, nullable=True)  # List of column names
    dtypes = Column(JSON, nullable=True)  # Data types
    missing_values = Column(JSON, nullable=True)  # Missing value counts
    
    # Metadata
    metadata_json = Column('metadata', JSON, nullable=True)
    summary_stats = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(String(50), default='received', nullable=False)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_dataset_user_id', 'user_id'),
        Index('idx_dataset_status', 'status'),
        Index('idx_dataset_created_at', 'created_at'),
    )

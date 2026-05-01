from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Index, Text
from sqlalchemy.sql import func
from ..database import Base

class ChatHistory(Base):
    """Chat history for GenAI interactions with datasets."""
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    dataset_id = Column(Integer, ForeignKey('datasets.id', ondelete='SET NULL'), nullable=True)
    
    user_query = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=True)
    generated_sql = Column(Text, nullable=True)
    
    metadata_json = Column('metadata', JSON, nullable=True)  # Retrieved context, tokens used, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_chat_user_id', 'user_id'),
        Index('idx_chat_dataset_id', 'dataset_id'),
        Index('idx_chat_created_at', 'created_at'),
    )

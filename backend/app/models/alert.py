from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Index, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from ..database import Base

class AlertRule(Base):
    """Alert rules for automatic notifications and triggers."""
    __tablename__ = 'alert_rules'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    alert_type = Column(String(100), nullable=False)  # 'sales_drop', 'high_demand', 'model_drift', etc.
    metric = Column(String(255), nullable=False)  # The metric to monitor
    condition = Column(String(50), nullable=False)  # 'greater_than', 'less_than', 'equal_to'
    threshold = Column(Float, nullable=False)

    active = Column(Boolean, default=True)
    cooldown_minutes = Column(Integer, default=60)  # Prevent alert spam

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_alert_active', 'active'),
        Index('idx_alert_rule_type', 'alert_type'),
    )

class Alert(Base):
    """Triggered alerts for notifications."""
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    alert_rule_id = Column(Integer, ForeignKey('alert_rules.id', ondelete='SET NULL'), nullable=True)

    alert_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False, default='medium')  # 'low', 'medium', 'high'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Alert data
    metric_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id', ondelete='SET NULL'), nullable=True)
    model_id = Column(Integer, ForeignKey('model_meta.id', ondelete='SET NULL'), nullable=True)

    # Status
    status = Column(String(50), nullable=False, default='active')  # 'active', 'acknowledged', 'resolved'
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    metadata_json = Column('metadata', JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_alert_user_id', 'user_id'),
        Index('idx_alert_status', 'status'),
        Index('idx_alert_type', 'alert_type'),
        Index('idx_alert_created_at', 'created_at'),
    )

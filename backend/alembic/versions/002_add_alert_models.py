"""Add Alert and AlertRule models.

Revision ID: 002_add_alert_models
Revises: 001_initial
Create Date: 2026-05-01

"""

from alembic import op
import sqlalchemy as sa

revision = '002_add_alert_models'
down_revision = '001_initial'
branch_labels = None
depends_on = None

def upgrade():
    """Upgrade database schema."""
    # Create alert_rules table
    op.create_table('alert_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('alert_type', sa.String(length=100), nullable=False),
        sa.Column('metric', sa.String(length=255), nullable=False),
        sa.Column('condition', sa.String(length=50), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_rules_id'), 'alert_rules', ['id'], unique=False)
    op.create_index('idx_alert_active', 'alert_rules', ['active'], unique=False)
    op.create_index('idx_alert_rule_type', 'alert_rules', ['alert_type'], unique=False)

    # Create alerts table
    op.create_table('alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('alert_rule_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('threshold_value', sa.Float(), nullable=True),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['alert_rule_id'], ['alert_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['model_id'], ['model_meta.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alerts_id'), 'alerts', ['id'], unique=False)
    op.create_index('idx_alert_user_id', 'alerts', ['user_id'], unique=False)
    op.create_index('idx_alert_status', 'alerts', ['status'], unique=False)
    op.create_index('idx_alert_type', 'alerts', ['alert_type'], unique=False)
    op.create_index('idx_alert_created_at', 'alerts', ['created_at'], unique=False)

def downgrade():
    """Downgrade database schema."""
    op.drop_index('idx_alert_created_at', table_name='alerts')
    op.drop_index('idx_alert_type', table_name='alerts')
    op.drop_index('idx_alert_status', table_name='alerts')
    op.drop_index('idx_alert_user_id', table_name='alerts')
    op.drop_index(op.f('ix_alerts_id'), table_name='alerts')
    op.drop_table('alerts')
    op.drop_index('idx_alert_rule_type', table_name='alert_rules')
    op.drop_index('idx_alert_active', table_name='alert_rules')
    op.drop_index(op.f('ix_alert_rules_id'), table_name='alert_rules')
    op.drop_table('alert_rules')
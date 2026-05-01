"""Initial migration: Create all tables.

Revision ID: 001_initial
Revises: 
Create Date: 2026-05-01

This is a reference migration. In production, use `alembic revision --autogenerate`
"""

from alembic import op
import sqlalchemy as sa

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Upgrade database schema."""
    pass

def downgrade():
    """Downgrade database schema."""
    pass

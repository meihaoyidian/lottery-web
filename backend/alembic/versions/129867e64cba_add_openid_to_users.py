"""add_openid_to_users

Revision ID: 129867e64cba
Revises: 002
Create Date: 2025-11-08 18:32:12.533559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '129867e64cba'
down_revision: Union[str, Sequence[str], None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add openid column to users table
    op.add_column('users', sa.Column('openid', sa.String(length=100), nullable=True, comment='微信OpenID'))
    op.create_index(op.f('ix_users_openid'), 'users', ['openid'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove openid column and index
    op.drop_index(op.f('ix_users_openid'), table_name='users')
    op.drop_column('users', 'openid')

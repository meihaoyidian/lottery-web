"""add_trial_user_fields

Revision ID: 004
Revises: d89bb711a89a
Create Date: 2025-11-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, Sequence[str], None] = 'd89bb711a89a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add trial user fields to users table
    op.add_column('users', sa.Column('is_trial_user', sa.Boolean(), nullable=False, server_default='0', comment='是否为体验用户'))
    op.add_column('users', sa.Column('trial_start_time', sa.DateTime(), nullable=True, comment='体验开始时间'))
    op.add_column('users', sa.Column('trial_end_time', sa.DateTime(), nullable=True, comment='体验结束时间'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove trial user fields
    op.drop_column('users', 'trial_end_time')
    op.drop_column('users', 'trial_start_time')
    op.drop_column('users', 'is_trial_user')

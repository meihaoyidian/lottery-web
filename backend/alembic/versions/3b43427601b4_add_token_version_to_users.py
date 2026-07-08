"""add_token_version_to_users

Revision ID: 3b43427601b4
Revises: 2ab492452436
Create Date: 2025-11-26 20:25:29.762896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b43427601b4'
down_revision: Union[str, Sequence[str], None] = '2ab492452436'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 token_version 字段
    op.add_column('users', sa.Column('token_version', sa.Integer(), server_default='0', nullable=False, comment='Token版本号，用于单设备登录控制'))


def downgrade() -> None:
    """Downgrade schema."""
    # 删除 token_version 字段
    op.drop_column('users', 'token_version')

"""add_description_to_daily_achievements

Revision ID: 2a6c1db8037e
Revises: 006
Create Date: 2025-11-20 00:47:35.860632

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a6c1db8037e'
down_revision: Union[str, Sequence[str], None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加description字段到daily_achievements表
    op.add_column('daily_achievements',
        sa.Column('description', sa.String(length=2000), nullable=True, comment='详细描述，最多2000字')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 删除description字段
    op.drop_column('daily_achievements', 'description')

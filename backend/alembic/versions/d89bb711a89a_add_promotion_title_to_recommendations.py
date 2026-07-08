"""add_promotion_title_to_recommendations

Revision ID: d89bb711a89a
Revises: 003_add_view_records
Create Date: 2025-11-11 23:38:42.410931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd89bb711a89a'
down_revision: Union[str, Sequence[str], None] = '003_add_view_records'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 promotion_title 字段到 recommendations 表
    op.add_column('recommendations',
        sa.Column('promotion_title', sa.String(100), nullable=True, comment='推广标题（选填，用于分享和推广展示）')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 删除 promotion_title 字段
    op.drop_column('recommendations', 'promotion_title')

"""add_daily_achievements_table

Revision ID: 006
Revises: 005
Create Date: 2025-11-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, Sequence[str], None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create daily_achievements table."""
    op.create_table(
        'daily_achievements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, comment='战绩ID'),
        sa.Column('date', sa.Date(), nullable=False, comment='战绩对应日期'),
        sa.Column('title', sa.String(100), nullable=False, comment="标题，如'昨日5中4'"),
        sa.Column('subtitle', sa.String(200), nullable=True, comment="副标题，如'足球3中3，篮球2中1'"),
        sa.Column('total_count', sa.Integer(), nullable=False, server_default='0', comment='总场次'),
        sa.Column('win_count', sa.Integer(), nullable=False, server_default='0', comment='命中场次'),
        sa.Column('accuracy_rate', mysql.DECIMAL(5, 2), nullable=False, server_default='0.00', comment='准确率（百分比）'),
        sa.Column('highlights', mysql.JSON(), nullable=True, comment='亮点数据，如[{"text": "连红3场", "icon": "🔥"}]'),
        sa.Column('banner_image', sa.String(500), nullable=True, comment='banner图片URL（可选）'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否显示'),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, comment='创建者ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', name='uq_daily_achievements_date'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # Create indexes
    op.create_index('ix_daily_achievements_id', 'daily_achievements', ['id'])
    op.create_index('ix_daily_achievements_date', 'daily_achievements', ['date'])
    op.create_index('ix_daily_achievements_is_active', 'daily_achievements', ['is_active'])


def downgrade() -> None:
    """Downgrade schema: Drop daily_achievements table."""
    op.drop_index('ix_daily_achievements_is_active', 'daily_achievements')
    op.drop_index('ix_daily_achievements_date', 'daily_achievements')
    op.drop_index('ix_daily_achievements_id', 'daily_achievements')
    op.drop_table('daily_achievements')

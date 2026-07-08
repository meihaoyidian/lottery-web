"""Add view_records table

Revision ID: 003_add_view_records
Revises: 129867e64cba
Create Date: 2025-01-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '003_add_view_records'
down_revision = '129867e64cba'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建浏览记录表"""
    op.create_table(
        'view_records',
        sa.Column('id', sa.Integer(), nullable=False, comment='记录ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='浏览用户ID'),
        sa.Column('recommendation_id', sa.Integer(), nullable=False, comment='推荐ID'),
        sa.Column('viewed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='浏览时间（UTC）'),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_view_records_id', 'view_records', ['id'], unique=False)
    op.create_index('ix_view_records_viewed_at', 'view_records', ['viewed_at'], unique=False)
    op.create_index('idx_recommendation_viewed', 'view_records', ['recommendation_id', 'viewed_at'], unique=False)
    op.create_index('idx_user_recommendation', 'view_records', ['user_id', 'recommendation_id'], unique=False)


def downgrade() -> None:
    """删除浏览记录表"""
    op.drop_index('idx_user_recommendation', table_name='view_records')
    op.drop_index('idx_recommendation_viewed', table_name='view_records')
    op.drop_index('ix_view_records_viewed_at', table_name='view_records')
    op.drop_index('ix_view_records_id', table_name='view_records')
    op.drop_table('view_records')

"""add key match fields

Revision ID: 007_add_key_match_fields
Revises: 2a6c1db8037e
Create Date: 2025-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_key_match_fields'
down_revision = '2a6c1db8037e'
branch_labels = None
depends_on = None


def upgrade():
    # 在 single_matches 的 JSON 结构中添加 is_key_match 字段
    # 注意：这是在 prediction_data JSON 字段内的结构变更，不需要ALTER TABLE
    # 只需要在应用层处理即可

    # 为 users 表添加 is_key_match_member 字段
    op.add_column('users', sa.Column('is_key_match_member', sa.Boolean(), nullable=False, server_default='0', comment='是否为重心场次付费用户（只能看重心场次）'))


def downgrade():
    # 移除 users 表的 is_key_match_member 字段
    op.drop_column('users', 'is_key_match_member')

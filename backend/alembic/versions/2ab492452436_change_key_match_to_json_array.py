"""change_key_match_to_json_array

Revision ID: 2ab492452436
Revises: eab4320101dc
Create Date: 2025-11-22 02:29:20.738425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ab492452436'
down_revision: Union[str, Sequence[str], None] = 'eab4320101dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 删除外键约束
    op.drop_constraint('fk_users_key_match_recommendation', 'users', type_='foreignkey')

    # 2. 创建新的 JSON 字段
    op.add_column('users', sa.Column('key_match_recommendation_ids', sa.JSON(), nullable=True, comment='绑定的重心场次推荐ID数组'))

    # 3. 迁移数据：将单个 ID 转换为数组格式
    # 使用原生 SQL 进行数据迁移
    op.execute("""
        UPDATE users
        SET key_match_recommendation_ids = JSON_ARRAY(key_match_recommendation_id)
        WHERE key_match_recommendation_id IS NOT NULL
    """)

    # 4. 删除旧字段
    op.drop_column('users', 'key_match_recommendation_id')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. 创建旧的 Integer 字段
    op.add_column('users', sa.Column('key_match_recommendation_id', sa.Integer(), nullable=True, comment='绑定的重心场次推荐ID'))

    # 2. 迁移数据：取数组中的第一个 ID
    op.execute("""
        UPDATE users
        SET key_match_recommendation_id = JSON_EXTRACT(key_match_recommendation_ids, '$[0]')
        WHERE key_match_recommendation_ids IS NOT NULL
        AND JSON_LENGTH(key_match_recommendation_ids) > 0
    """)

    # 3. 添加外键约束
    op.create_foreign_key(
        'fk_users_key_match_recommendation',
        'users', 'recommendations',
        ['key_match_recommendation_id'], ['id'],
        ondelete='SET NULL'
    )

    # 4. 删除 JSON 字段
    op.drop_column('users', 'key_match_recommendation_ids')

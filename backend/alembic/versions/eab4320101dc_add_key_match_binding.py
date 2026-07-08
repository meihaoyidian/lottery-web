"""add_key_match_binding

Revision ID: eab4320101dc
Revises: 007_add_key_match_fields
Create Date: 2025-11-22 02:18:17.286654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eab4320101dc'
down_revision: Union[str, Sequence[str], None] = '007_add_key_match_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加 key_match_recommendation_id 字段，记录重心场次用户绑定的推荐ID
    op.add_column('users', sa.Column('key_match_recommendation_id', sa.Integer(), nullable=True, comment='绑定的重心场次推荐ID'))
    # 添加外键约束
    op.create_foreign_key(
        'fk_users_key_match_recommendation',
        'users', 'recommendations',
        ['key_match_recommendation_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 删除外键约束
    op.drop_constraint('fk_users_key_match_recommendation', 'users', type_='foreignkey')
    # 删除字段
    op.drop_column('users', 'key_match_recommendation_id')

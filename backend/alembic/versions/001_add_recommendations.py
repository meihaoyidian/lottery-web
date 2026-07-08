"""Add recommendations table and extend users table

Revision ID: 001
Revises:
Create Date: 2025-10-25 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema:
    1. Extend users table with is_paid and role columns
    2. Create recommendations table with JSON fields
    """

    # Extend users table
    op.add_column('users', sa.Column('is_paid', sa.Boolean(), nullable=False, server_default='0', comment='是否为付费用户'))
    op.add_column('users', sa.Column('role', sa.Enum('user', 'admin', name='user_role'), nullable=False, server_default='user', comment='用户角色'))

    # Add indexes for new columns
    op.create_index('idx_is_paid', 'users', ['is_paid'])
    op.create_index('idx_role', 'users', ['role'])

    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, comment='推荐ID'),
        sa.Column('created_by_id', sa.Integer(), nullable=False, comment='创建管理员ID'),
        sa.Column('sport_type', sa.Enum('football', 'basketball', name='sport_type'), nullable=False, comment='运动类型'),
        sa.Column('match_info', mysql.JSON(), nullable=False, comment='比赛信息 {team_a, team_b, league, match_datetime}'),
        sa.Column('prediction_data', mysql.JSON(), nullable=False, comment='预测数据（运动类型特定）'),
        sa.Column('analysis_text', sa.Text(), nullable=False, comment='分析说明（支持富文本）'),
        sa.Column('status', sa.Enum('active', 'inactive', 'completed', name='recommendation_status'), nullable=False, server_default='active', comment='推荐状态'),
        sa.Column('actual_outcome', mysql.JSON(), nullable=True, comment='实际结果（用于历史记录）'),
        sa.Column('archived_at', sa.DateTime(), nullable=True, comment='归档时间（90天后归档）'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='UTC时间戳'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='RESTRICT'),

        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # Create indexes for recommendations table
    op.create_index('idx_sport_type', 'recommendations', ['sport_type'])
    op.create_index('idx_status', 'recommendations', ['status'])
    op.create_index('idx_archived', 'recommendations', ['archived_at'])
    op.create_index('idx_created_at', 'recommendations', ['created_at'])

    # Create functional index for match_datetime (extracted from JSON)
    # Use raw SQL for functional indexes in MySQL
    op.execute("""
        CREATE INDEX idx_match_time
        ON recommendations ((CAST(match_info->'$.match_datetime' AS DATETIME)))
    """)

    # Create unique constraint for duplicate prevention
    # NOTE: MySQL 8.0+ supports functional indexes and unique constraints on generated columns
    op.execute("""
        CREATE UNIQUE INDEX uk_match_unique
        ON recommendations (
            sport_type,
            (CAST(MD5(CONCAT(LOWER(match_info->>'$.team_a'), '|', LOWER(match_info->>'$.team_b'))) AS CHAR(32))),
            (DATE(CAST(match_info->'$.match_datetime' AS DATETIME)))
        )
    """)


def downgrade() -> None:
    """
    Downgrade schema:
    1. Drop recommendations table
    2. Remove is_paid and role columns from users table
    """

    # Drop recommendations table
    op.drop_index('uk_match_unique', table_name='recommendations')
    op.drop_index('idx_match_time', table_name='recommendations')
    op.drop_index('idx_created_at', table_name='recommendations')
    op.drop_index('idx_archived', table_name='recommendations')
    op.drop_index('idx_status', table_name='recommendations')
    op.drop_index('idx_sport_type', table_name='recommendations')
    op.drop_table('recommendations')

    # Remove columns from users table
    op.drop_index('idx_role', table_name='users')
    op.drop_index('idx_is_paid', table_name='users')
    op.drop_column('users', 'role')
    op.drop_column('users', 'is_paid')

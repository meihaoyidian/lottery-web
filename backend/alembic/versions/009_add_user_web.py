"""create user_web table (copy of users, web-only fields)

Revision ID: 009_add_user_web
Revises: 3b43427601b4
Create Date: 2026-07-09

Web 端用户体系独立化：新建 user_web 表并从 users 拷贝数据，
去掉 openid / 重心场次会员等小程序字段。同时删除三张业务表指向
users.id 的外键约束（仅删约束，不动数据），使 Web 表与 users 解耦。

注意：
- 拷贝逻辑与建表解耦，采用"表空才拷贝"的幂等策略，避免 create_all
  提前建了空表后拷贝被跳过。
- down_revision 直接指向 3b43427601b4，不经过 008（不改动共享的 users 表）。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009_add_user_web'
down_revision: Union[str, Sequence[str], None] = '3b43427601b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 需要解除对 users.id 外键的业务表：(表名, 列名)
_FK_TABLES = [
    ('recommendations', 'created_by_id'),
    ('view_records', 'user_id'),
    ('daily_achievements', 'created_by_id'),
]

# 拷贝的列（user_web 与 users 共有）
_COPY_COLUMNS = (
    "id, phone, password_hash, nickname, is_paid, paid_start_time, "
    "paid_end_time, token_version, role, created_at, updated_at"
)


def _drop_fk_to_users(inspector, table, column):
    """删除指定表上引用 users 表的外键约束（存在才删）。"""
    try:
        fks = inspector.get_foreign_keys(table)
    except Exception:
        return
    for fk in fks:
        if fk.get('referred_table') == 'users' and column in fk.get('constrained_columns', []):
            if fk.get('name'):
                op.drop_constraint(fk['name'], table, type_='foreignkey')


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. 建 user_web 表（若 create_all 已提前建好则跳过建表）
    if not inspector.has_table('user_web'):
        op.create_table(
            'user_web',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, comment='用户ID'),
            sa.Column('phone', sa.String(length=20), nullable=False, comment='手机号'),
            sa.Column('password_hash', sa.String(length=255), nullable=False, comment='密码哈希'),
            sa.Column('nickname', sa.String(length=50), nullable=True, comment='昵称'),
            sa.Column('is_paid', sa.Boolean(), nullable=False, server_default='0', comment='是否为付费用户'),
            sa.Column('paid_start_time', sa.DateTime(), nullable=True, comment='付费开始时间'),
            sa.Column('paid_end_time', sa.DateTime(), nullable=True, comment='付费结束时间'),
            sa.Column('token_version', sa.Integer(), nullable=False, server_default='0', comment='Token版本号'),
            sa.Column('role', sa.Enum('user', 'admin', name='userrole'), nullable=False, server_default='user', comment='用户角色'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False, comment='更新时间'),
        )
        op.create_index('ix_user_web_phone', 'user_web', ['phone'], unique=True)
        op.create_index('ix_user_web_id', 'user_web', ['id'], unique=False)

    # 2. 拷贝数据（与建表解耦、幂等）：仅当 user_web 为空且 users 有数据时执行
    if inspector.has_table('users'):
        existing = conn.execute(sa.text("SELECT COUNT(*) FROM user_web")).scalar()
        if existing == 0:
            op.execute(
                f"INSERT INTO user_web ({_COPY_COLUMNS}) "
                f"SELECT {_COPY_COLUMNS} FROM users"
            )
            # 拷贝保留了原始 id，重置 AUTO_INCREMENT 到 max(id)+1，避免后续新注册冲突
            max_id = conn.execute(sa.text("SELECT COALESCE(MAX(id), 0) FROM user_web")).scalar()
            op.execute(f"ALTER TABLE user_web AUTO_INCREMENT = {int(max_id) + 1}")

    # 3. 删除三张业务表指向 users.id 的外键约束（数据不动）
    for table, column in _FK_TABLES:
        if inspector.has_table(table):
            _drop_fk_to_users(inspector, table, column)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 恢复外键约束
    if inspector.has_table('recommendations'):
        op.create_foreign_key(
            'fk_recommendations_created_by', 'recommendations', 'users',
            ['created_by_id'], ['id'], ondelete='RESTRICT'
        )
    if inspector.has_table('view_records'):
        op.create_foreign_key(
            'fk_view_records_user', 'view_records', 'users',
            ['user_id'], ['id'], ondelete='SET NULL'
        )
    if inspector.has_table('daily_achievements'):
        op.create_foreign_key(
            'fk_daily_achievements_created_by', 'daily_achievements', 'users',
            ['created_by_id'], ['id']
        )

    # 删除 user_web 表
    if inspector.has_table('user_web'):
        op.drop_table('user_web')

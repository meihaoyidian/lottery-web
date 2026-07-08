"""添加订阅消息表

Revision ID: 002
Revises: 001
Create Date: 2025-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建订阅消息记录表
    op.create_table(
        'recommendation_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False, comment='订阅ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('openid', sa.String(length=100), nullable=False, comment='微信OpenID'),
        sa.Column('template_id', sa.String(length=100), nullable=False, comment='模板ID'),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False, comment='是否启用'),
        sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='推荐订阅消息表'
    )

    # 创建索引
    op.create_index(op.f('ix_recommendation_subscriptions_user_id'), 'recommendation_subscriptions', ['user_id'], unique=False)
    op.create_index(op.f('ix_recommendation_subscriptions_openid'), 'recommendation_subscriptions', ['openid'], unique=False)
    op.create_index(op.f('ix_recommendation_subscriptions_is_active'), 'recommendation_subscriptions', ['is_active'], unique=False)

    # 创建唯一约束：每个用户对同一模板只能有一条订阅记录
    op.create_index('ix_user_template_unique', 'recommendation_subscriptions', ['user_id', 'template_id'], unique=True)

    # 创建订阅消息发送记录表
    op.create_table(
        'subscription_messages',
        sa.Column('id', sa.Integer(), nullable=False, comment='消息ID'),
        sa.Column('subscription_id', sa.Integer(), nullable=False, comment='订阅ID'),
        sa.Column('recommendation_id', sa.Integer(), nullable=False, comment='推荐ID'),
        sa.Column('openid', sa.String(length=100), nullable=False, comment='接收者OpenID'),
        sa.Column('template_id', sa.String(length=100), nullable=False, comment='模板ID'),
        sa.Column('page', sa.String(length=200), nullable=True, comment='跳转页面路径'),
        sa.Column('data', sa.JSON(), nullable=False, comment='消息内容'),
        sa.Column('status', sa.Enum('pending', 'sent', 'failed', name='message_status'), nullable=False, server_default='pending', comment='发送状态'),
        sa.Column('error_msg', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('sent_at', mysql.DATETIME(), nullable=True, comment='发送时间'),
        sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        comment='订阅消息发送记录表'
    )

    # 创建索引
    op.create_index(op.f('ix_subscription_messages_subscription_id'), 'subscription_messages', ['subscription_id'], unique=False)
    op.create_index(op.f('ix_subscription_messages_recommendation_id'), 'subscription_messages', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_subscription_messages_status'), 'subscription_messages', ['status'], unique=False)
    op.create_index(op.f('ix_subscription_messages_created_at'), 'subscription_messages', ['created_at'], unique=False)


def downgrade() -> None:
    # 删除订阅消息发送记录表
    op.drop_index(op.f('ix_subscription_messages_created_at'), table_name='subscription_messages')
    op.drop_index(op.f('ix_subscription_messages_status'), table_name='subscription_messages')
    op.drop_index(op.f('ix_subscription_messages_recommendation_id'), table_name='subscription_messages')
    op.drop_index(op.f('ix_subscription_messages_subscription_id'), table_name='subscription_messages')
    op.drop_table('subscription_messages')

    # 删除订阅消息记录表
    op.drop_index('ix_user_template_unique', table_name='recommendation_subscriptions')
    op.drop_index(op.f('ix_recommendation_subscriptions_is_active'), table_name='recommendation_subscriptions')
    op.drop_index(op.f('ix_recommendation_subscriptions_openid'), table_name='recommendation_subscriptions')
    op.drop_index(op.f('ix_recommendation_subscriptions_user_id'), table_name='recommendation_subscriptions')
    op.drop_table('recommendation_subscriptions')

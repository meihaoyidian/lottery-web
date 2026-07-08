"""extend_phone_field_length_for_international_numbers

Revision ID: 005
Revises: 004
Create Date: 2025-11-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, Sequence[str], None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Extend phone field length to support international numbers."""
    # Modify phone column to support international phone numbers (up to 20 characters)
    # This allows for phone numbers like +60124155917 (Malaysia) and other international formats
    op.alter_column('users', 'phone',
                    existing_type=sa.String(11),
                    type_=sa.String(20),
                    existing_nullable=False,
                    comment='手机号（支持国际号码）')


def downgrade() -> None:
    """Downgrade schema: Revert phone field length to 11 characters."""
    # Note: Downgrading may cause data loss if there are phone numbers longer than 11 characters
    op.alter_column('users', 'phone',
                    existing_type=sa.String(20),
                    type_=sa.String(11),
                    existing_nullable=False,
                    comment='手机号')

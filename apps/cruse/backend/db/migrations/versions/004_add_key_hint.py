# pylint: disable=invalid-name,missing-function-docstring,no-member
"""Add key_hint column to api_keys table.

Revision ID: 004
Revises: 003
Create Date: 2026-03-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("api_keys", sa.Column("key_hint", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("api_keys", "key_hint")

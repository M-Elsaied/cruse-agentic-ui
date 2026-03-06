# pylint: disable=invalid-name,missing-function-docstring,no-member
"""Add message_id and is_error columns to request_log.

Revision ID: 002
Revises: 001
Create Date: 2026-03-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("request_log", sa.Column("message_id", sa.BigInteger(), nullable=True))
    op.add_column("request_log", sa.Column("is_error", sa.Boolean(), nullable=False, server_default="false"))
    op.create_foreign_key(
        "fk_request_log_message_id",
        "request_log",
        "messages",
        ["message_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_request_log_message_id", "request_log", type_="foreignkey")
    op.drop_column("request_log", "is_error")
    op.drop_column("request_log", "message_id")

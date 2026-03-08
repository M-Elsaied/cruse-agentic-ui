# pylint: disable=invalid-name,missing-function-docstring,no-member
"""Add agent_networks table for custom user-created networks.

Revision ID: 005
Revises: 004
Create Date: 2026-03-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_networks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("org_id", sa.BigInteger(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("hocon_content", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_shared", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "last_materialized_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("created_by", "slug", name="uq_agent_networks_user_slug"),
    )
    op.create_index("idx_agent_networks_org", "agent_networks", ["org_id"])
    op.create_index("idx_agent_networks_creator", "agent_networks", ["created_by"])


def downgrade() -> None:
    op.drop_index("idx_agent_networks_creator", table_name="agent_networks")
    op.drop_index("idx_agent_networks_org", table_name="agent_networks")
    op.drop_table("agent_networks")

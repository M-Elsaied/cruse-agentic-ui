# pylint: disable=invalid-name,missing-function-docstring,no-member
"""Add organizations, org_memberships tables and org_id FK to existing tables.

Revision ID: 003
Revises: 002
Create Date: 2026-03-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("clerk_org_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=True),
        sa.Column("settings", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.dialects.postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.dialects.postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clerk_org_id"),
        sa.UniqueConstraint("slug"),
    )

    # 2. Create org_memberships table
    op.create_table(
        "org_memberships",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("org_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("org_role", sa.String(50), nullable=False, server_default="member"),
        sa.Column(
            "joined_at",
            sa.dialects.postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.clerk_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("org_id", "user_id"),
    )
    op.create_index("idx_org_memberships_user", "org_memberships", ["user_id"])

    # 3. Add default_org_id to users
    op.add_column("users", sa.Column("default_org_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key("fk_users_default_org_id", "users", "organizations", ["default_org_id"], ["id"])

    # 4. Add nullable org_id FK to existing tables
    for table_name in (
        "conversations",
        "daily_usage",
        "api_keys",
        "user_preferences",
        "feedback_reports",
        "request_log",
    ):
        op.add_column(table_name, sa.Column("org_id", sa.BigInteger(), nullable=True))
        op.create_foreign_key(f"fk_{table_name}_org_id", table_name, "organizations", ["org_id"], ["id"])


def downgrade() -> None:
    # Remove org_id FK from existing tables
    for table_name in (
        "request_log",
        "feedback_reports",
        "user_preferences",
        "api_keys",
        "daily_usage",
        "conversations",
    ):
        op.drop_constraint(f"fk_{table_name}_org_id", table_name, type_="foreignkey")
        op.drop_column(table_name, "org_id")

    # Remove default_org_id from users
    op.drop_constraint("fk_users_default_org_id", "users", type_="foreignkey")
    op.drop_column("users", "default_org_id")

    # Drop tables
    op.drop_index("idx_org_memberships_user", "org_memberships")
    op.drop_table("org_memberships")
    op.drop_table("organizations")

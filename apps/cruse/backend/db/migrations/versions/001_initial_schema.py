"""Initial schema with all 9 tables.

Revision ID: 001
Revises:
Create Date: 2026-03-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("clerk_id", sa.String(255), primary_key=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="user"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── daily_usage ───────────────────────────────────────────────
    op.create_table(
        "daily_usage",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.clerk_id"), nullable=False),
        sa.Column("usage_date", sa.Date, nullable=False, server_default=sa.func.current_date()),
        sa.Column("request_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "usage_date"),
    )
    op.create_index("idx_daily_usage_lookup", "daily_usage", ["user_id", "usage_date"])

    # ── api_keys ──────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.clerk_id"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("encrypted_key", sa.Text, nullable=False),
        sa.Column("key_version", sa.SmallInteger, nullable=False, server_default="1"),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("is_valid", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "provider"),
    )
    op.create_index("idx_api_keys_user", "api_keys", ["user_id"])

    # ── user_preferences ──────────────────────────────────────────
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.clerk_id"), primary_key=True),
        sa.Column("preferred_provider", sa.String(50), nullable=True),
        sa.Column("preferred_model", sa.String(100), nullable=True),
        sa.Column("settings", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── conversations ─────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(255), nullable=False, unique=True),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.clerk_id"), nullable=False),
        sa.Column("agent_network", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_conversations_user", "conversations", ["user_id", "created_at"])
    op.create_index("idx_conversations_session", "conversations", ["session_id"])

    # ── messages ──────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "conversation_id",
            sa.BigInteger,
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_messages_conversation", "messages", ["conversation_id", "created_at"])

    # ── message_feedback ──────────────────────────────────────────
    op.create_table(
        "message_feedback",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("message_id", sa.BigInteger, sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.clerk_id"), nullable=False),
        sa.Column("rating", sa.SmallInteger, sa.CheckConstraint("rating IN (-1, 1)"), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("message_id", "user_id"),
    )

    # ── feedback_reports ──────────────────────────────────────────
    op.create_table(
        "feedback_reports",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.clerk_id"), nullable=False),
        sa.Column(
            "conversation_id",
            sa.BigInteger,
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("message_id", sa.BigInteger, sa.ForeignKey("messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(50), nullable=False, server_default="bug"),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("context", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_feedback_reports_user", "feedback_reports", ["user_id", "created_at"])
    op.create_index("idx_feedback_reports_status", "feedback_reports", ["status"])

    # ── request_log ───────────────────────────────────────────────
    op.create_table(
        "request_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(255), sa.ForeignKey("users.clerk_id"), nullable=False),
        sa.Column(
            "conversation_id",
            sa.BigInteger,
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("agent_network", sa.String(255), nullable=False),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("prompt_tokens", sa.Integer, nullable=True),
        sa.Column("completion_tokens", sa.Integer, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_request_log_user", "request_log", ["user_id", "created_at"])
    op.create_index("idx_request_log_date", "request_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("request_log")
    op.drop_table("feedback_reports")
    op.drop_table("message_feedback")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("user_preferences")
    op.drop_table("api_keys")
    op.drop_table("daily_usage")
    op.drop_table("users")

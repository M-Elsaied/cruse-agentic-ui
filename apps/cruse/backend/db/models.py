# Copyright © 2025-2026 Cognizant Technology Solutions Corp, www.cognizant.com.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# END COPYRIGHT

# pylint: disable=not-callable,unsubscriptable-object,too-few-public-methods

from datetime import date
from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import CheckConstraint
from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import SmallInteger
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from apps.cruse.backend.db.base import Base


class Organization(Base):
    """Organization record, upserted from Clerk JWT org claims."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    clerk_org_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(255), unique=True)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),  # pylint: disable=not-callable
    )


class OrgMembership(Base):
    """Tracks which users belong to which organizations and their role within."""

    __tablename__ = "org_memberships"
    __table_args__ = (
        UniqueConstraint("org_id", "user_id"),
        Index("idx_org_memberships_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    org_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.clerk_id", ondelete="CASCADE"), nullable=False)
    org_role: Mapped[str] = mapped_column(String(50), nullable=False, server_default="member")
    joined_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class User(Base):
    """User record, upserted from Clerk JWT on first authenticated request."""

    __tablename__ = "users"

    clerk_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), nullable=False, server_default="user")
    default_org_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),  # pylint: disable=not-callable
    )


class DailyUsage(Base):
    """Per-user per-day request counter, replaces Clerk publicMetadata hack."""

    __tablename__ = "daily_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date"),
        Index("idx_daily_usage_lookup", "user_id", "usage_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.clerk_id"), nullable=False)
    org_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    usage_date: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class ApiKey(Base):
    """Fernet-encrypted BYOK API key storage."""

    __tablename__ = "api_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "provider"),
        Index("idx_api_keys_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.clerk_id"), nullable=False)
    org_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_version: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")
    label: Mapped[str | None] = mapped_column(String(255))
    key_hint: Mapped[str | None] = mapped_column(String(10))
    is_valid: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),  # pylint: disable=not-callable
    )


class UserPreference(Base):
    """Per-user LLM provider/model preferences and extensible settings."""

    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.clerk_id"), primary_key=True)
    org_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    preferred_provider: Mapped[str | None] = mapped_column(String(50))
    preferred_model: Mapped[str | None] = mapped_column(String(100))
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),  # pylint: disable=not-callable
    )


class Conversation(Base):
    """One row per chat session."""

    __tablename__ = "conversations"
    __table_args__ = (
        Index("idx_conversations_user", "user_id", "created_at"),
        Index("idx_conversations_session", "session_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.clerk_id"), nullable=False)
    org_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    agent_network: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),  # pylint: disable=not-callable
    )

    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete")


class Message(Base):
    """Normalized per-message storage with JSONB metadata for extensibility."""

    __tablename__ = "messages"
    __table_args__ = (Index("idx_messages_conversation", "conversation_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


class MessageFeedback(Base):
    """Thumbs up/down per message."""

    __tablename__ = "message_feedback"
    __table_args__ = (UniqueConstraint("message_id", "user_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.clerk_id"), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, CheckConstraint("rating IN (-1, 1)"), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class FeedbackReport(Base):
    """Standalone written bug/feature reports."""

    __tablename__ = "feedback_reports"
    __table_args__ = (
        Index("idx_feedback_reports_user", "user_id", "created_at"),
        Index("idx_feedback_reports_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.clerk_id"), nullable=False)
    org_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    conversation_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("conversations.id", ondelete="SET NULL")
    )
    message_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("messages.id", ondelete="SET NULL"))
    category: Mapped[str] = mapped_column(String(50), nullable=False, server_default="bug")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="open")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class AgentNetwork(Base):
    """User-created custom agent network with HOCON content."""

    __tablename__ = "agent_networks"
    __table_args__ = (
        UniqueConstraint("created_by", "slug", name="uq_agent_networks_user_slug"),
        Index("idx_agent_networks_org", "org_id"),
        Index("idx_agent_networks_creator", "created_by"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    org_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    hocon_content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_materialized_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),  # pylint: disable=not-callable
    )


class RequestLog(Base):
    """Per-request analytics for admin dashboards."""

    __tablename__ = "request_log"
    __table_args__ = (
        Index("idx_request_log_user", "user_id", "created_at"),
        Index("idx_request_log_date", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("users.clerk_id"), nullable=False)
    org_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id"))
    conversation_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("conversations.id", ondelete="SET NULL")
    )
    message_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("messages.id", ondelete="SET NULL"))
    agent_network: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    is_error: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

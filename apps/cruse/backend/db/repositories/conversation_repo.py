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

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from sqlalchemy import func
from sqlalchemy import literal_column
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.cruse.backend.db.models import Conversation
from apps.cruse.backend.db.models import Message
from apps.cruse.backend.db.models import User


class ConversationRepository:
    """Repository for conversation CRUD."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, session_id: str, user_id: str, agent_network: str) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(session_id=session_id, user_id=user_id, agent_network=agent_network)
        self._db.add(conversation)
        await self._db.flush()
        return conversation

    async def list(
        self,
        user_id: str,
        *,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """List conversations for a user, most recent first."""
        stmt = select(Conversation).where(Conversation.user_id == user_id)
        if not include_archived:
            stmt = stmt.where(Conversation.is_archived.is_(False))
        stmt = stmt.order_by(Conversation.created_at.desc()).limit(limit).offset(offset)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, conversation_id: int) -> Conversation | None:
        """Get a conversation by ID."""
        result = await self._db.execute(select(Conversation).where(Conversation.id == conversation_id))
        return result.scalar_one_or_none()

    async def get_by_session_id(self, session_id: str) -> Conversation | None:
        """Get a conversation by session ID."""
        result = await self._db.execute(select(Conversation).where(Conversation.session_id == session_id))
        return result.scalar_one_or_none()

    async def get_with_messages(self, conversation_id: int) -> Conversation | None:
        """Get a conversation with all its messages eagerly loaded."""
        result = await self._db.execute(
            select(Conversation).where(Conversation.id == conversation_id).options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def archive(self, conversation_id: int) -> bool:
        """Soft-delete a conversation by marking it archived."""
        result = await self._db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(is_archived=True, updated_at=func.now())  # pylint: disable=not-callable
        )
        await self._db.flush()
        return result.rowcount > 0

    async def update_title(self, conversation_id: int, title: str) -> bool:
        """Set or update the conversation title."""
        result = await self._db.execute(
            update(Conversation).where(Conversation.id == conversation_id).values(title=title, updated_at=func.now())  # pylint: disable=not-callable
        )
        await self._db.flush()
        return result.rowcount > 0

    async def list_with_counts(
        self,
        user_id: str,
        *,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list:
        """List conversations with message counts, most recent first."""
        count_subq = (
            select(Message.conversation_id, func.count(Message.id).label("msg_count"))  # pylint: disable=not-callable
            .group_by(Message.conversation_id)
            .subquery()
        )
        stmt = (
            select(Conversation, func.coalesce(count_subq.c.msg_count, 0).label("message_count"))
            .outerjoin(count_subq, Conversation.id == count_subq.c.conversation_id)
            .where(Conversation.user_id == user_id)
        )
        if not include_archived:
            stmt = stmt.where(Conversation.is_archived.is_(False))
        stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
        result = await self._db.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    # ─── Admin Methods ─────────────────────────────────────────────

    async def list_all(  # pylint: disable=too-many-arguments
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        user_id: str | None = None,
        agent_network: str | None = None,
        include_archived: bool = False,
    ) -> tuple[list, int]:
        """Admin: list all conversations with user info and message counts."""
        count_subq = (
            select(Message.conversation_id, func.count(Message.id).label("msg_count"))  # pylint: disable=not-callable
            .group_by(Message.conversation_id)
            .subquery()
        )
        stmt = (
            select(
                Conversation,
                func.coalesce(count_subq.c.msg_count, 0).label("message_count"),
                User.email,
                User.name,
            )
            .outerjoin(count_subq, Conversation.id == count_subq.c.conversation_id)
            .outerjoin(User, Conversation.user_id == User.clerk_id)
        )

        # Filters
        if user_id:
            stmt = stmt.where(Conversation.user_id == user_id)
        if agent_network:
            stmt = stmt.where(Conversation.agent_network == agent_network)
        if not include_archived:
            stmt = stmt.where(Conversation.is_archived.is_(False))

        # Total count (same filters, no pagination)
        count_base = select(Conversation.id)
        if user_id:
            count_base = count_base.where(Conversation.user_id == user_id)
        if agent_network:
            count_base = count_base.where(Conversation.agent_network == agent_network)
        if not include_archived:
            count_base = count_base.where(Conversation.is_archived.is_(False))
        count_stmt = select(func.count(literal_column("1"))).select_from(  # pylint: disable=not-callable
            count_base.subquery()
        )
        count_result = await self._db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
        result = await self._db.execute(stmt)
        rows = [(row[0], row[1], row[2], row[3]) for row in result.all()]
        return rows, total

    # ─── Analytics Methods ────────────────────────────────────────

    async def get_avg_depth_by_network(self, *, period_days: int = 30) -> list[dict]:
        """Get average conversation depth (message count) per network."""
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)

        # Subquery: message count per conversation
        msg_count_sq = (
            select(
                Message.conversation_id,
                func.count(Message.id).label("msg_count"),  # pylint: disable=not-callable
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        stmt = (
            select(
                Conversation.agent_network.label("network"),
                func.avg(msg_count_sq.c.msg_count).label("avg_messages"),
                func.count(Conversation.id).label("conversation_count"),  # pylint: disable=not-callable
            )
            .join(msg_count_sq, Conversation.id == msg_count_sq.c.conversation_id)
            .where(Conversation.created_at >= cutoff)
            .group_by(Conversation.agent_network)
        )
        result = await self._db.execute(stmt)
        return [
            {
                "network": row.network,
                "avg_messages": round(float(row.avg_messages), 1) if row.avg_messages else 0.0,
                "conversation_count": row.conversation_count,
            }
            for row in result.all()
        ]

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

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.cruse.backend.db.models import Conversation


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
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def archive(self, conversation_id: int) -> bool:
        """Soft-delete a conversation by marking it archived."""
        result = await self._db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(is_archived=True, updated_at=func.now())
        )
        await self._db.flush()
        return result.rowcount > 0

    async def update_title(self, conversation_id: int, title: str) -> bool:
        """Set or update the conversation title."""
        result = await self._db.execute(
            update(Conversation).where(Conversation.id == conversation_id).values(title=title, updated_at=func.now())
        )
        await self._db.flush()
        return result.rowcount > 0

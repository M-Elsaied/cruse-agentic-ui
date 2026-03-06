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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.models import Message


class MessageRepository:
    """Repository for message storage and retrieval."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def append(
        self,
        conversation_id: int,
        role: str,
        content: str,
        *,
        metadata: dict | None = None,
    ) -> Message:
        """Append a message to a conversation."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_=metadata or {},
        )
        self._db.add(message)
        await self._db.flush()
        return message

    async def get_by_id(self, message_id: int) -> Message | None:
        """Get a single message by ID."""
        result = await self._db.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()

    async def list_by_conversation(self, conversation_id: int, *, limit: int = 100, offset: int = 0) -> list[Message]:
        """List messages for a conversation in chronological order."""
        result = await self._db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

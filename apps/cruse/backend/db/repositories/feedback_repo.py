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
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.models import FeedbackReport
from apps.cruse.backend.db.models import MessageFeedback


class FeedbackRepository:
    """Repository for message feedback and bug/feature reports."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def add_rating(
        self, message_id: int, user_id: str, rating: int, *, comment: str | None = None
    ) -> MessageFeedback:
        """Add or update a thumbs up/down rating on a message.

        If the user already rated this message, the rating is updated.
        """
        stmt = (
            insert(MessageFeedback)
            .values(message_id=message_id, user_id=user_id, rating=rating, comment=comment)
            .on_conflict_do_update(
                constraint="message_feedback_message_id_user_id_key",
                set_={"rating": rating, "comment": comment},
            )
            .returning(MessageFeedback)
        )
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.scalar_one()

    async def add_report(  # pylint: disable=too-many-arguments
        self,
        user_id: str,
        body: str,
        *,
        category: str = "bug",
        conversation_id: int | None = None,
        message_id: int | None = None,
        context: dict | None = None,
    ) -> FeedbackReport:
        """Create a written feedback report."""
        report = FeedbackReport(
            user_id=user_id,
            body=body,
            category=category,
            conversation_id=conversation_id,
            message_id=message_id,
            context=context or {},
        )
        self._db.add(report)
        await self._db.flush()
        return report

    async def list_reports(
        self,
        *,
        status: str | None = None,
        user_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeedbackReport]:
        """List feedback reports with optional filters."""
        stmt = select(FeedbackReport)
        if status is not None:
            stmt = stmt.where(FeedbackReport.status == status)
        if user_id is not None:
            stmt = stmt.where(FeedbackReport.user_id == user_id)
        stmt = stmt.order_by(FeedbackReport.created_at.desc()).limit(limit).offset(offset)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

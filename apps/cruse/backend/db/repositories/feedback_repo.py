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

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from sqlalchemy import case
from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.models import Conversation
from apps.cruse.backend.db.models import FeedbackReport
from apps.cruse.backend.db.models import Message
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
        org_id: int | None = None,
    ) -> FeedbackReport:
        """Create a written feedback report."""
        report = FeedbackReport(
            user_id=user_id,
            body=body,
            category=category,
            conversation_id=conversation_id,
            message_id=message_id,
            context=context or {},
            org_id=org_id,
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

    async def count_reports(
        self,
        *,
        status: str | None = None,
        user_id: str | None = None,
    ) -> int:
        """Count feedback reports with optional filters."""
        stmt = select(func.count(FeedbackReport.id))  # pylint: disable=not-callable
        if status is not None:
            stmt = stmt.where(FeedbackReport.status == status)
        if user_id is not None:
            stmt = stmt.where(FeedbackReport.user_id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def delete_rating(self, message_id: int, user_id: str) -> bool:
        """Delete a user's rating on a message. Returns True if a row was deleted."""
        stmt = (
            delete(MessageFeedback)
            .where(MessageFeedback.message_id == message_id)
            .where(MessageFeedback.user_id == user_id)
        )
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.rowcount > 0

    # ─── Analytics Methods ────────────────────────────────────────

    async def get_satisfaction_score(self, *, period_days: int = 30) -> dict:
        """Get aggregate satisfaction score for the period."""
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        stmt = select(
            func.sum(case((MessageFeedback.rating == 1, 1), else_=0)).label("thumbs_up"),
            func.sum(case((MessageFeedback.rating == -1, 1), else_=0)).label("thumbs_down"),
            func.count(MessageFeedback.id).label("total"),  # pylint: disable=not-callable
        ).where(MessageFeedback.created_at >= cutoff)
        result = await self._db.execute(stmt)
        row = result.one()
        total = row.total or 0
        thumbs_up = row.thumbs_up or 0
        thumbs_down = row.thumbs_down or 0
        return {
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down,
            "total": total,
            "score": round(thumbs_up / total, 4) if total > 0 else -1.0,
        }

    async def get_network_satisfaction(self, *, period_days: int = 30) -> list[dict]:
        """Get per-network satisfaction scores.

        Joins message_feedback -> messages -> conversations to resolve the agent_network.
        """
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        stmt = (
            select(
                Conversation.agent_network.label("network"),
                func.sum(case((MessageFeedback.rating == 1, 1), else_=0)).label("thumbs_up"),
                func.sum(case((MessageFeedback.rating == -1, 1), else_=0)).label("thumbs_down"),
                func.count(MessageFeedback.id).label("total"),  # pylint: disable=not-callable
            )
            .join(Message, MessageFeedback.message_id == Message.id)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(MessageFeedback.created_at >= cutoff)
            .group_by(Conversation.agent_network)
        )
        result = await self._db.execute(stmt)
        return [
            {
                "network": row.network,
                "thumbs_up": row.thumbs_up or 0,
                "thumbs_down": row.thumbs_down or 0,
                "score": round((row.thumbs_up or 0) / row.total, 4) if row.total > 0 else -1.0,
            }
            for row in result.all()
        ]

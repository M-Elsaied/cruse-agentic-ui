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

from sqlalchemy import Date as SADate
from sqlalchemy import case
from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.models import Conversation
from apps.cruse.backend.db.models import RequestLog
from apps.cruse.backend.db.models import User


class RequestLogRepository:
    """Repository for per-request analytics logging."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def log_request(  # pylint: disable=too-many-arguments
        self,
        user_id: str,
        agent_network: str,
        *,
        conversation_id: int | None = None,
        message_id: int | None = None,
        model: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        latency_ms: int | None = None,
        is_error: bool = False,
        org_id: int | None = None,
    ) -> RequestLog:
        """Record a single request for analytics."""
        entry = RequestLog(
            user_id=user_id,
            agent_network=agent_network,
            conversation_id=conversation_id,
            message_id=message_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            is_error=is_error,
            org_id=org_id,
        )
        self._db.add(entry)
        await self._db.flush()
        return entry

    async def get_stats(self, *, start: datetime | None = None, end: datetime | None = None) -> dict:
        """Get aggregate stats for the given date range."""
        stmt = select(
            func.count(RequestLog.id).label("total_requests"),  # pylint: disable=not-callable
            func.count(func.distinct(RequestLog.user_id)).label("unique_users"),  # pylint: disable=not-callable
            func.sum(RequestLog.prompt_tokens).label("total_prompt_tokens"),
            func.sum(RequestLog.completion_tokens).label("total_completion_tokens"),
            func.avg(RequestLog.latency_ms).label("avg_latency_ms"),
        )
        if start is not None:
            stmt = stmt.where(RequestLog.created_at >= start)
        if end is not None:
            stmt = stmt.where(RequestLog.created_at < end)
        result = await self._db.execute(stmt)
        row = result.one()
        return {
            "total_requests": row.total_requests,
            "unique_users": row.unique_users,
            "total_prompt_tokens": row.total_prompt_tokens or 0,
            "total_completion_tokens": row.total_completion_tokens or 0,
            "avg_latency_ms": round(float(row.avg_latency_ms), 1) if row.avg_latency_ms else 0,
        }

    async def get_user_stats(self, user_id: str) -> dict:
        """Get per-user aggregate stats."""
        stmt = select(
            func.count(RequestLog.id).label("total_requests"),  # pylint: disable=not-callable
            func.sum(RequestLog.prompt_tokens).label("total_prompt_tokens"),
            func.sum(RequestLog.completion_tokens).label("total_completion_tokens"),
            func.avg(RequestLog.latency_ms).label("avg_latency_ms"),
        ).where(RequestLog.user_id == user_id)
        result = await self._db.execute(stmt)
        row = result.one()
        return {
            "total_requests": row.total_requests,
            "total_prompt_tokens": row.total_prompt_tokens or 0,
            "total_completion_tokens": row.total_completion_tokens or 0,
            "avg_latency_ms": round(float(row.avg_latency_ms), 1) if row.avg_latency_ms else 0,
        }

    # ─── Analytics Methods ────────────────────────────────────────

    async def get_overview(self, *, period_days: int = 30) -> dict:
        """Get KPI overview with period-over-period comparison.

        Returns counts, averages, and error rate for both the current
        and previous period of the same length.
        """
        now = datetime.now(tz=timezone.utc)
        current_start = now - timedelta(days=period_days)
        prev_start = current_start - timedelta(days=period_days)

        is_current = case(
            (RequestLog.created_at >= current_start, 1),
            else_=0,
        )
        is_prev = case(
            (RequestLog.created_at < current_start, 1),
            else_=0,
        )
        is_error_int = case(
            (RequestLog.is_error.is_(True), 1),
            else_=0,
        )

        stmt = select(
            func.sum(is_current).label("total_requests"),
            func.sum(is_prev).label("prev_total_requests"),
            func.count(  # pylint: disable=not-callable
                func.distinct(case((RequestLog.created_at >= current_start, RequestLog.user_id)))
            ).label("unique_users"),
            func.count(  # pylint: disable=not-callable
                func.distinct(case((RequestLog.created_at < current_start, RequestLog.user_id)))
            ).label("prev_unique_users"),
            func.avg(case((RequestLog.created_at >= current_start, RequestLog.latency_ms))).label("avg_latency_ms"),
            func.avg(case((RequestLog.created_at < current_start, RequestLog.latency_ms))).label(
                "prev_avg_latency_ms"
            ),
            func.sum(is_current * is_error_int).label("error_count"),
            func.sum(is_prev * is_error_int).label("prev_error_count"),
        ).where(RequestLog.created_at >= prev_start)

        result = await self._db.execute(stmt)
        row = result.one()

        total = row.total_requests or 0
        prev_total = row.prev_total_requests or 0
        errors = row.error_count or 0
        prev_errors = row.prev_error_count or 0

        return {
            "total_requests": total,
            "unique_users": row.unique_users or 0,
            "avg_latency_ms": round(float(row.avg_latency_ms), 1) if row.avg_latency_ms else 0.0,
            "error_count": errors,
            "error_rate": round(errors / total, 4) if total > 0 else 0.0,
            "prev_total_requests": prev_total,
            "prev_unique_users": row.prev_unique_users or 0,
            "prev_avg_latency_ms": round(float(row.prev_avg_latency_ms), 1) if row.prev_avg_latency_ms else 0.0,
            "prev_error_count": prev_errors,
            "prev_error_rate": round(prev_errors / prev_total, 4) if prev_total > 0 else 0.0,
        }

    async def get_requests_over_time(self, *, period_days: int = 30) -> list[dict]:
        """Get daily request count + error count for the period."""
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        day_col = cast(RequestLog.created_at, SADate).label("day")
        stmt = (
            select(
                day_col,
                func.count(RequestLog.id).label("count"),  # pylint: disable=not-callable
                func.sum(case((RequestLog.is_error.is_(True), 1), else_=0)).label("error_count"),
            )
            .where(RequestLog.created_at >= cutoff)
            .group_by(day_col)
            .order_by(day_col)
        )
        result = await self._db.execute(stmt)
        return [
            {"date": str(row.day), "count": row.count, "error_count": row.error_count or 0} for row in result.all()
        ]

    async def get_active_users_over_time(self, *, period_days: int = 30) -> list[dict]:
        """Get daily active users (DAU) for the period."""
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        day_col = cast(RequestLog.created_at, SADate).label("day")
        stmt = (
            select(
                day_col,
                func.count(func.distinct(RequestLog.user_id)).label("count"),  # pylint: disable=not-callable
            )
            .where(RequestLog.created_at >= cutoff)
            .group_by(day_col)
            .order_by(day_col)
        )
        result = await self._db.execute(stmt)
        return [{"date": str(row.day), "count": row.count} for row in result.all()]

    async def get_top_networks(self, *, period_days: int = 30, limit: int = 20) -> list[dict]:
        """Get per-network request stats sorted by count DESC."""
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        stmt = (
            select(
                RequestLog.agent_network.label("network"),
                func.count(RequestLog.id).label("request_count"),  # pylint: disable=not-callable
                func.avg(RequestLog.latency_ms).label("avg_latency_ms"),
                func.sum(case((RequestLog.is_error.is_(True), 1), else_=0)).label("error_count"),
            )
            .where(RequestLog.created_at >= cutoff)
            .group_by(RequestLog.agent_network)
            .order_by(func.count(RequestLog.id).desc())  # pylint: disable=not-callable
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return [
            {
                "network": row.network,
                "request_count": row.request_count,
                "avg_latency_ms": round(float(row.avg_latency_ms), 1) if row.avg_latency_ms else 0.0,
                "error_rate": round((row.error_count or 0) / row.request_count, 4) if row.request_count > 0 else 0.0,
            }
            for row in result.all()
        ]

    async def get_user_breakdown(
        self,
        *,
        period_days: int = 30,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Get per-user request breakdown with pagination."""
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)

        # Subquery for conversation counts per user
        conv_count_sq = (
            select(
                Conversation.user_id,
                func.count(Conversation.id).label("conv_count"),  # pylint: disable=not-callable
            )
            .where(Conversation.created_at >= cutoff)
            .group_by(Conversation.user_id)
            .subquery()
        )

        # Main query: request stats joined with user info + conversation counts
        stmt = (
            select(
                RequestLog.user_id,
                func.count(RequestLog.id).label("request_count"),  # pylint: disable=not-callable
                func.avg(RequestLog.latency_ms).label("avg_latency_ms"),
                func.max(RequestLog.created_at).label("last_active"),
                func.coalesce(conv_count_sq.c.conv_count, 0).label("conversation_count"),
                User.email,
                User.name,
            )
            .outerjoin(User, RequestLog.user_id == User.clerk_id)
            .outerjoin(conv_count_sq, RequestLog.user_id == conv_count_sq.c.user_id)
            .where(RequestLog.created_at >= cutoff)
            .group_by(RequestLog.user_id, conv_count_sq.c.conv_count, User.email, User.name)
            .order_by(func.count(RequestLog.id).desc())  # pylint: disable=not-callable
        )

        # Total count
        from sqlalchemy import literal_column  # pylint: disable=import-outside-toplevel

        count_stmt = select(func.count(literal_column("1"))).select_from(  # pylint: disable=not-callable
            select(RequestLog.user_id).where(RequestLog.created_at >= cutoff).group_by(RequestLog.user_id).subquery()
        )
        count_result = await self._db.execute(count_stmt)
        total = count_result.scalar_one()

        result = await self._db.execute(stmt.limit(limit).offset(offset))
        users = [
            {
                "user_id": row.user_id,
                "email": row.email,
                "name": row.name,
                "request_count": row.request_count,
                "conversation_count": row.conversation_count,
                "avg_latency_ms": round(float(row.avg_latency_ms), 1) if row.avg_latency_ms else 0.0,
                "last_active": row.last_active.isoformat() if row.last_active else None,
            }
            for row in result.all()
        ]
        return users, total

    async def get_export_rows(self, *, period_days: int = 90, limit: int = 10000) -> list[dict]:
        """Get raw request log rows for CSV export."""
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=period_days)
        stmt = (
            select(
                RequestLog.created_at,
                RequestLog.user_id,
                RequestLog.agent_network,
                RequestLog.latency_ms,
                RequestLog.is_error,
            )
            .where(RequestLog.created_at >= cutoff)
            .order_by(RequestLog.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return [
            {
                "date": row.created_at.isoformat(),
                "user_id": row.user_id,
                "agent_network": row.agent_network,
                "latency_ms": row.latency_ms,
                "is_error": row.is_error,
            }
            for row in result.all()
        ]

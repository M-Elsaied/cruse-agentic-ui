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

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.models import RequestLog


class RequestLogRepository:
    """Repository for per-request analytics logging."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def log_request(
        self,
        user_id: str,
        agent_network: str,
        *,
        conversation_id: int | None = None,
        model: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        latency_ms: int | None = None,
    ) -> RequestLog:
        """Record a single request for analytics."""
        entry = RequestLog(
            user_id=user_id,
            agent_network=agent_network,
            conversation_id=conversation_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
        )
        self._db.add(entry)
        await self._db.flush()
        return entry

    async def get_stats(self, *, start: datetime | None = None, end: datetime | None = None) -> dict:
        """Get aggregate stats for the given date range."""
        stmt = select(
            func.count(RequestLog.id).label("total_requests"),
            func.count(func.distinct(RequestLog.user_id)).label("unique_users"),
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
            func.count(RequestLog.id).label("total_requests"),
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

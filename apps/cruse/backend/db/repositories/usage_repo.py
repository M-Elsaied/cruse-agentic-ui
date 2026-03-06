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

from datetime import UTC
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.models import DailyUsage


class UsageRepository:
    """Repository for per-user daily usage tracking."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def increment_and_check(self, user_id: str, max_daily: int) -> tuple[bool, int]:
        """Atomically increment the daily counter and check against the limit.

        Uses a single ``INSERT ... ON CONFLICT DO UPDATE ... WHERE`` so the
        increment only succeeds when ``request_count < max_daily``, eliminating
        TOCTOU race conditions between concurrent requests.

        Returns ``(allowed, remaining)``. If the user is already at or above
        the limit, the counter is **not** incremented.
        """
        today = datetime.now(UTC).date()

        stmt = (
            insert(DailyUsage)
            .values(user_id=user_id, usage_date=today, request_count=1)
            .on_conflict_do_update(
                constraint="daily_usage_user_id_usage_date_key",
                set_={"request_count": DailyUsage.request_count + 1},
                where=(DailyUsage.request_count < max_daily),
            )
            .returning(DailyUsage.request_count)
        )
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        await self._db.flush()

        if row is not None:
            return True, max(0, max_daily - row)

        # No row returned — WHERE didn't match, so the limit was already reached
        return False, 0

    async def get_remaining(self, user_id: str, max_daily: int) -> tuple[int, int]:
        """Return ``(remaining, limit)`` without incrementing."""
        today = datetime.now(UTC).date()
        result = await self._db.execute(
            select(DailyUsage.request_count).where(
                DailyUsage.user_id == user_id,
                DailyUsage.usage_date == today,
            )
        )
        count = result.scalar_one_or_none() or 0
        return max(0, max_daily - count), max_daily

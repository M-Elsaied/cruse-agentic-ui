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

import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.repositories.usage_repo import UsageRepository

logger = logging.getLogger(__name__)


class RateLimiter:
    """Per-user daily request rate limiter backed by PostgreSQL.

    Uses atomic UPSERT on the ``daily_usage`` table for race-free counting.
    Admin users bypass rate limiting entirely.
    """

    def __init__(self):
        self._max_daily: int = 0
        self._enabled: bool = False

    async def init(self):
        """Read config from environment."""
        self._max_daily = int(os.environ.get("MAX_DAILY_REQUESTS", "5"))
        if self._max_daily <= 0:
            logger.info("Rate limiting disabled (MAX_DAILY_REQUESTS=%s)", self._max_daily)
            self._enabled = False
            return

        self._enabled = True
        logger.info("Rate limiting enabled: %d requests/day per user", self._max_daily)

    async def check_and_increment(
        self, user_id: str, role: str, db: AsyncSession
    ) -> tuple[bool, int | None, int | None]:
        """Check whether a user may send a message and increment usage.

        Returns ``(allowed, remaining, limit)``.
        *remaining* and *limit* are ``None`` for admin users or when limiting
        is disabled.
        """
        if not self._enabled or role == "admin":
            return True, None, None

        repo = UsageRepository(db)
        allowed, remaining = await repo.increment_and_check(user_id, self._max_daily)
        return allowed, remaining, self._max_daily

    async def get_remaining(self, user_id: str, role: str, db: AsyncSession) -> tuple[int | None, int | None]:
        """Return ``(remaining, limit)`` without incrementing.

        Used by the ``/api/me`` endpoint to seed the frontend on page load.
        """
        if not self._enabled or role == "admin":
            return None, None

        repo = UsageRepository(db)
        remaining, limit = await repo.get_remaining(user_id, self._max_daily)
        return remaining, limit

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

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

CLERK_API_BASE = "https://api.clerk.com/v1"


@dataclass
class UserUsage:
    """Tracks daily usage for a single user."""

    count: int = 0
    reset_date: str = ""  # ISO date string (YYYY-MM-DD) in UTC
    dirty: bool = False  # Whether this needs syncing back to Clerk


class RateLimiter:
    """Per-user daily request rate limiter backed by Clerk publicMetadata.

    Uses an in-memory dict for fast per-message checks. On first access for
    each user, lazy-loads the count from Clerk ``publicMetadata.daily_usage``.
    A background loop periodically syncs dirty counts back to Clerk via
    the Clerk REST API (using httpx).
    """

    def __init__(self):
        self._usage: dict[str, UserUsage] = {}
        self._max_daily: int = 0
        self._sync_task: asyncio.Task | None = None
        self._secret_key: str = ""
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

        self._secret_key = os.environ.get("CLERK_SECRET_KEY", "")
        if not self._secret_key:
            logger.warning("CLERK_SECRET_KEY not set; rate-limit counts will not persist across restarts")

    # ── Public API ───────────────────────────────────────────────

    async def check_and_increment(self, user_id: str, role: str) -> tuple[bool, int | None, int | None]:
        """Check whether a user may send a message and increment usage.

        Returns ``(allowed, remaining, limit)``.
        *remaining* and *limit* are ``None`` for admin users or when limiting
        is disabled.
        """
        if not self._enabled or role == "admin":
            return True, None, None

        usage = await self._get_or_load(user_id)
        self._maybe_reset(usage)

        if usage.count >= self._max_daily:
            return False, 0, self._max_daily

        usage.count += 1
        usage.dirty = True
        remaining = self._max_daily - usage.count
        return True, remaining, self._max_daily

    def get_remaining(self, user_id: str, role: str) -> tuple[int | None, int | None]:
        """Return ``(remaining, limit)`` without incrementing.

        Used by the ``/api/me`` endpoint to seed the frontend on page load.
        """
        if not self._enabled or role == "admin":
            return None, None

        usage = self._usage.get(user_id)
        if usage is None:
            return self._max_daily, self._max_daily

        self._maybe_reset(usage)
        return self._max_daily - usage.count, self._max_daily

    # ── Background sync ──────────────────────────────────────────

    def start_sync_loop(self):
        """Start the background task that periodically flushes dirty counts to Clerk."""
        if self._enabled and self._secret_key:
            self._sync_task = asyncio.create_task(self._sync_loop())

    async def stop(self):
        """Cancel the sync loop and perform a final flush."""
        if self._sync_task is not None:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        await self._flush_to_clerk()

    async def _sync_loop(self):
        """Flush dirty counts to Clerk every 60 seconds."""
        try:
            while True:
                await asyncio.sleep(60)
                await self._flush_to_clerk()
        except asyncio.CancelledError:
            pass

    async def _flush_to_clerk(self):
        """Write all dirty in-memory counts back to Clerk publicMetadata."""
        if not self._secret_key:
            return

        dirty_users = {uid: u for uid, u in self._usage.items() if u.dirty}
        if not dirty_users:
            return

        async with httpx.AsyncClient() as client:
            for user_id, usage in dirty_users.items():
                try:
                    resp = await client.patch(
                        f"{CLERK_API_BASE}/users/{user_id}/metadata",
                        headers={"Authorization": f"Bearer {self._secret_key}"},
                        json={
                            "public_metadata": {
                                "daily_usage": {
                                    "count": usage.count,
                                    "date": usage.reset_date,
                                }
                            }
                        },
                        timeout=10.0,
                    )
                    resp.raise_for_status()
                    usage.dirty = False
                except Exception:  # pylint: disable=broad-exception-caught
                    logger.warning("Failed to sync usage to Clerk for user %s", user_id)

    # ── Internal helpers ─────────────────────────────────────────

    async def _get_or_load(self, user_id: str) -> UserUsage:
        """Return cached usage or lazy-load from Clerk on first access."""
        if user_id in self._usage:
            return self._usage[user_id]

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        usage = UserUsage(count=0, reset_date=today)

        if self._secret_key:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{CLERK_API_BASE}/users/{user_id}",
                        headers={"Authorization": f"Bearer {self._secret_key}"},
                        timeout=10.0,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    daily = (data.get("public_metadata") or {}).get("daily_usage", {})
                    if isinstance(daily, dict) and daily.get("date") == today:
                        usage.count = int(daily.get("count", 0))
                        logger.debug("Loaded usage for %s from Clerk: %d", user_id, usage.count)
            except Exception:  # pylint: disable=broad-exception-caught
                logger.warning("Failed to load usage from Clerk for %s; starting from 0", user_id)

        self._usage[user_id] = usage
        return usage

    @staticmethod
    def _maybe_reset(usage: UserUsage):
        """Reset the counter if the UTC date has rolled over."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if usage.reset_date != today:
            usage.count = 0
            usage.reset_date = today
            usage.dirty = True

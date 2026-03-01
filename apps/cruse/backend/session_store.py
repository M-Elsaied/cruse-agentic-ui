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
import time

logger = logging.getLogger(__name__)

# Default session timeout: 30 minutes
DEFAULT_TIMEOUT_SECONDS = 1800


class SessionTimeoutManager:
    """Monitors sessions and cleans up those that have been idle too long."""

    def __init__(self, session_manager, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS):
        self._session_manager = session_manager
        self._timeout = timeout_seconds
        self._last_activity: dict[str, float] = {}
        self._task: asyncio.Task | None = None

    def touch(self, session_id: str):
        """Record activity for a session."""
        self._last_activity[session_id] = time.time()

    def remove(self, session_id: str):
        """Stop tracking a session."""
        self._last_activity.pop(session_id, None)

    async def start(self):
        """Start the background cleanup loop."""
        self._task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the background cleanup loop."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self):
        """Periodically check for and destroy timed-out sessions."""
        while True:
            await asyncio.sleep(60)  # Check every minute
            now = time.time()
            expired = [sid for sid, last in self._last_activity.items() if now - last > self._timeout]
            for sid in expired:
                logger.info("Session %s timed out after %ds of inactivity", sid, self._timeout)
                self._session_manager.destroy_session(sid)
                self._last_activity.pop(sid, None)

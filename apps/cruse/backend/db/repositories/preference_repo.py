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
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.models import UserPreference


class PreferenceRepository:
    """Repository for user preferences."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get(self, user_id: str) -> UserPreference | None:
        """Get preferences for a user. Returns None if no preferences stored."""
        result = await self._db.execute(select(UserPreference).where(UserPreference.user_id == user_id))
        return result.scalar_one_or_none()

    async def update(
        self,
        user_id: str,
        *,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
        settings: dict | None = None,
    ) -> UserPreference:
        """Upsert user preferences. Only provided fields are updated."""
        values: dict = {"user_id": user_id}
        update_set: dict = {"updated_at": func.now()}  # pylint: disable=not-callable

        if preferred_provider is not None:
            values["preferred_provider"] = preferred_provider
            update_set["preferred_provider"] = preferred_provider
        if preferred_model is not None:
            values["preferred_model"] = preferred_model
            update_set["preferred_model"] = preferred_model
        if settings is not None:
            values["settings"] = settings
            update_set["settings"] = settings

        stmt = (
            insert(UserPreference)
            .values(**values)
            .on_conflict_do_update(index_elements=["user_id"], set_=update_set)
            .returning(UserPreference)
        )
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.scalar_one()

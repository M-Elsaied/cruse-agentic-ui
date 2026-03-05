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

from apps.cruse.backend.db.models import User


class UserRepository:
    """Repository for user CRUD operations."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def upsert_from_clerk(self, clerk_id: str, email: str | None, name: str | None, role: str) -> User:
        """Insert a new user or update an existing one from Clerk JWT data."""
        stmt = (
            insert(User)
            .values(clerk_id=clerk_id, email=email, name=name, role=role)
            .on_conflict_do_update(
                index_elements=["clerk_id"],
                set_={
                    "email": email,
                    "name": name,
                    "role": role,
                    "updated_at": func.now(),
                },
            )
            .returning(User)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, clerk_id: str) -> User | None:
        """Fetch a user by Clerk ID."""
        result = await self._db.execute(select(User).where(User.clerk_id == clerk_id))
        return result.scalar_one_or_none()

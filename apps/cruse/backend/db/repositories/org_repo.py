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

from apps.cruse.backend.db.models import Organization
from apps.cruse.backend.db.models import OrgMembership


class OrgRepository:
    """Repository for organization CRUD operations."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def upsert_from_clerk(self, clerk_org_id: str, name: str, slug: str | None = None) -> Organization:
        """Insert a new organization or update an existing one from Clerk claims."""
        stmt = (
            insert(Organization)
            .values(clerk_org_id=clerk_org_id, name=name, slug=slug)
            .on_conflict_do_update(
                index_elements=["clerk_org_id"],
                set_={
                    "name": name,
                    "slug": slug,
                    "updated_at": func.now(),  # pylint: disable=not-callable
                },
            )
            .returning(Organization)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def get_by_clerk_id(self, clerk_org_id: str) -> Organization | None:
        """Fetch an organization by its Clerk org ID."""
        result = await self._db.execute(select(Organization).where(Organization.clerk_org_id == clerk_org_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, org_id: int) -> Organization | None:
        """Fetch an organization by internal ID."""
        result = await self._db.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()

    async def upsert_membership(self, org_id: int, user_id: str, org_role: str = "member") -> OrgMembership:
        """Ensure a user is a member of an organization with the given role."""
        stmt = (
            insert(OrgMembership)
            .values(org_id=org_id, user_id=user_id, org_role=org_role)
            .on_conflict_do_update(
                constraint="org_memberships_org_id_user_id_key",
                set_={"org_role": org_role},
            )
            .returning(OrgMembership)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def list_for_user(self, user_id: str) -> list[Organization]:
        """List all organizations a user belongs to."""
        stmt = (
            select(Organization)
            .join(OrgMembership, OrgMembership.org_id == Organization.id)
            .where(OrgMembership.user_id == user_id)
            .order_by(Organization.name)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

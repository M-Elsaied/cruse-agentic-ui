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
from datetime import timezone

from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.models import AgentNetwork


class AgentNetworkRepository:
    """Repository for user-created custom agent networks."""

    MAX_NETWORKS_PER_USER = 50

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(  # pylint: disable=too-many-arguments
        self,
        created_by: str,
        name: str,
        slug: str,
        hocon_content: str,
        *,
        org_id: int | None = None,
        description: str | None = None,
    ) -> AgentNetwork:
        """Create a new custom agent network."""
        network = AgentNetwork(
            created_by=created_by,
            name=name,
            slug=slug,
            hocon_content=hocon_content,
            org_id=org_id,
            description=description,
        )
        self._db.add(network)
        await self._db.flush()
        return network

    async def get_by_id(self, network_id: int) -> AgentNetwork | None:
        """Get a network by ID (excludes archived)."""
        result = await self._db.execute(
            select(AgentNetwork).where(AgentNetwork.id == network_id, AgentNetwork.is_archived.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, created_by: str, slug: str) -> AgentNetwork | None:
        """Get a network by owner and slug (excludes archived)."""
        result = await self._db.execute(
            select(AgentNetwork).where(
                AgentNetwork.created_by == created_by,
                AgentNetwork.slug == slug,
                AgentNetwork.is_archived.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_owned(self, user_id: str) -> list[AgentNetwork]:
        """List all active networks owned by this user."""
        result = await self._db.execute(
            select(AgentNetwork)
            .where(AgentNetwork.created_by == user_id, AgentNetwork.is_archived.is_(False))
            .order_by(AgentNetwork.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_shared(self, user_id: str, org_id: int) -> list[AgentNetwork]:
        """List active networks shared within the user's org (excludes user's own)."""
        result = await self._db.execute(
            select(AgentNetwork)
            .where(
                AgentNetwork.org_id == org_id,
                AgentNetwork.is_shared.is_(True),
                AgentNetwork.is_archived.is_(False),
                AgentNetwork.created_by != user_id,
            )
            .order_by(AgentNetwork.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_all_active(self) -> list[AgentNetwork]:
        """List all active (non-archived) networks. Used for startup materialization."""
        result = await self._db.execute(
            select(AgentNetwork).where(AgentNetwork.is_archived.is_(False)).order_by(AgentNetwork.id)
        )
        return list(result.scalars().all())

    async def update_content(self, network_id: int, hocon_content: str, *, name: str | None = None) -> bool:
        """Update the HOCON content (and optionally name) of a network."""
        values: dict = {"hocon_content": hocon_content, "updated_at": func.now()}  # pylint: disable=not-callable
        if name is not None:
            values["name"] = name
        result = await self._db.execute(
            update(AgentNetwork)
            .where(AgentNetwork.id == network_id, AgentNetwork.is_archived.is_(False))
            .values(**values)
        )
        await self._db.flush()
        return result.rowcount > 0

    async def update_metadata(
        self,
        network_id: int,
        *,
        description: str | None = ...,
        is_shared: bool | None = None,
    ) -> bool:
        """Update metadata fields (description, sharing toggle)."""
        values: dict = {"updated_at": func.now()}  # pylint: disable=not-callable
        if description is not ...:
            values["description"] = description
        if is_shared is not None:
            values["is_shared"] = is_shared
        result = await self._db.execute(
            update(AgentNetwork)
            .where(AgentNetwork.id == network_id, AgentNetwork.is_archived.is_(False))
            .values(**values)
        )
        await self._db.flush()
        return result.rowcount > 0

    async def set_materialized(self, network_id: int) -> None:
        """Mark a network as materialized to disk."""
        await self._db.execute(
            update(AgentNetwork)
            .where(AgentNetwork.id == network_id)
            .values(last_materialized_at=datetime.now(tz=timezone.utc))
        )
        await self._db.flush()

    async def archive(self, network_id: int) -> bool:
        """Soft-delete a network by marking it archived."""
        result = await self._db.execute(
            update(AgentNetwork)
            .where(AgentNetwork.id == network_id, AgentNetwork.is_archived.is_(False))
            .values(is_archived=True, updated_at=func.now())  # pylint: disable=not-callable
        )
        await self._db.flush()
        return result.rowcount > 0

    async def count_for_user(self, user_id: str) -> int:
        """Count active networks for a user (for enforcing MAX_NETWORKS_PER_USER)."""
        result = await self._db.execute(
            select(func.count(AgentNetwork.id)).where(  # pylint: disable=not-callable
                AgentNetwork.created_by == user_id,
                AgentNetwork.is_archived.is_(False),
            )
        )
        return result.scalar_one()

    async def is_accessible(self, network_id: int, user_id: str, org_id: int | None) -> bool:
        """Check if a user can access a network (owner or shared in same org)."""
        conditions = [AgentNetwork.id == network_id, AgentNetwork.is_archived.is_(False)]
        owner_cond = AgentNetwork.created_by == user_id
        shared_cond = (
            and_(
                AgentNetwork.is_shared.is_(True),
                AgentNetwork.org_id == org_id,
            )
            if org_id is not None
            else None
        )

        if shared_cond is not None:
            stmt = select(AgentNetwork.id).where(*conditions).where(owner_cond | shared_cond)
        else:
            stmt = select(AgentNetwork.id).where(*conditions).where(owner_cond)

        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

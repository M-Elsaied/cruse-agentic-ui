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
from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.auth import ClerkUser
from apps.cruse.backend.auth import get_current_user
from apps.cruse.backend.db.engine import get_db
from apps.cruse.backend.db.models import Organization
from apps.cruse.backend.db.repositories.org_repo import OrgRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

PERSONAL_ORG_PREFIX = "personal_"


@dataclass
class TenantContext:
    """Resolved tenant context for the current request.

    Contains the authenticated user, their active organization,
    and derived permission flags.
    """

    user: ClerkUser
    org: Organization
    is_org_admin: bool

    @property
    def user_id(self) -> str:
        """Shortcut: Clerk user ID for ownership checks."""
        return self.user.user_id

    @property
    def org_id(self) -> int:
        """Shortcut: internal DB org ID for query filtering."""
        return self.org.id


async def resolve_tenant_context(user: ClerkUser, db: AsyncSession) -> TenantContext:
    """Resolve a ClerkUser into a full TenantContext.

    1. If user has org_id from JWT -> upsert Organization from Clerk claims
    2. If no org_id -> create/use personal org ("personal_{user_id}")
    3. Upsert OrgMembership
    4. Return TenantContext
    """
    org_repo = OrgRepository(db)
    user_repo = UserRepository(db)

    if user.org_id:
        org_name = user.org_slug or user.org_id
        org = await org_repo.upsert_from_clerk(user.org_id, org_name, slug=user.org_slug)
        org_role = _normalize_org_role(user.org_role)
    else:
        personal_clerk_id = f"{PERSONAL_ORG_PREFIX}{user.user_id}"
        org = await org_repo.get_by_clerk_id(personal_clerk_id)
        if org is None:
            org = await org_repo.upsert_from_clerk(
                personal_clerk_id,
                f"{user.name or user.user_id}'s Workspace",
                slug=None,
            )
        org_role = "admin"

    await org_repo.upsert_membership(org.id, user.user_id, org_role)

    # Update user's default org if not already set
    db_user = await user_repo.get_by_id(user.user_id)
    if db_user and db_user.default_org_id is None:
        db_user.default_org_id = org.id
        await db.flush()

    is_org_admin = org_role in ("admin", "owner")

    return TenantContext(user=user, org=org, is_org_admin=is_org_admin)


async def get_tenant(
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> "TenantContext":
    """FastAPI dependency that resolves user + org into a TenantContext."""
    await UserRepository(db).upsert_from_clerk(user.user_id, user.email, user.name, user.role)
    return await resolve_tenant_context(user, db)


def _normalize_org_role(clerk_role: str | None) -> str:
    """Normalize Clerk org role (e.g. 'org:admin') to simple role string."""
    if not clerk_role:
        return "member"
    role = clerk_role.removeprefix("org:")
    if role in ("admin", "owner"):
        return role
    return "member"

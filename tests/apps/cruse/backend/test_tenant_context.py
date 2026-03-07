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

# pylint: disable=missing-function-docstring,redefined-outer-name

"""Phase 2: Tenant Context Tests.

Tests the resolve_tenant_context function and org role normalization.
Requires PostgreSQL — skips if not available.
"""

import pytest
import pytest_asyncio

from apps.cruse.backend.auth import ClerkUser
from apps.cruse.backend.db.repositories.user_repo import UserRepository
from apps.cruse.backend.tenant_context import PERSONAL_ORG_PREFIX
from apps.cruse.backend.tenant_context import resolve_tenant_context


@pytest.fixture
def make_user():
    def _make(user_id="user1", role="user", org_id=None, org_role=None, org_slug=None):
        return ClerkUser(
            user_id=user_id,
            email=f"{user_id}@test.com",
            role=role,
            name=user_id,
            org_id=org_id,
            org_role=org_role,
            org_slug=org_slug,
        )

    return _make


@pytest_asyncio.fixture
async def seeded_db(db):
    """Ensure a user exists in the DB for tenant resolution."""
    await UserRepository(db).upsert_from_clerk("alice", "alice@test.com", "Alice", "user")
    await UserRepository(db).upsert_from_clerk("bob", "bob@test.com", "Bob", "user")
    await db.flush()
    return db


@pytest.mark.asyncio
async def test_resolve_with_clerk_org(seeded_db, make_user):
    user = make_user(user_id="alice", org_id="org_clerk123", org_role="org:admin", org_slug="my-org")
    tenant = await resolve_tenant_context(user, seeded_db)

    assert tenant.org.clerk_org_id == "org_clerk123"
    assert tenant.org.name == "my-org"
    assert tenant.is_org_admin is True
    assert tenant.user.user_id == "alice"


@pytest.mark.asyncio
async def test_resolve_without_org_creates_personal(seeded_db, make_user):
    user = make_user(user_id="alice")
    tenant = await resolve_tenant_context(user, seeded_db)

    assert tenant.org.clerk_org_id == f"{PERSONAL_ORG_PREFIX}alice"
    assert tenant.is_org_admin is True  # personal org -> admin


@pytest.mark.asyncio
async def test_resolve_is_idempotent(seeded_db, make_user):
    user = make_user(user_id="alice", org_id="org_x", org_role="org:member", org_slug="test-org")
    tenant1 = await resolve_tenant_context(user, seeded_db)
    tenant2 = await resolve_tenant_context(user, seeded_db)

    assert tenant1.org.id == tenant2.org.id


@pytest.mark.asyncio
async def test_org_member_not_admin(seeded_db, make_user):
    user = make_user(user_id="bob", org_id="org_y", org_role="org:member", org_slug="other-org")
    tenant = await resolve_tenant_context(user, seeded_db)

    assert tenant.is_org_admin is False


@pytest.mark.asyncio
async def test_switch_org_changes_context(seeded_db, make_user):
    user_org_a = make_user(user_id="alice", org_id="org_a", org_role="org:admin", org_slug="org-a")
    user_org_b = make_user(user_id="alice", org_id="org_b", org_role="org:member", org_slug="org-b")

    tenant_a = await resolve_tenant_context(user_org_a, seeded_db)
    tenant_b = await resolve_tenant_context(user_org_b, seeded_db)

    assert tenant_a.org.clerk_org_id == "org_a"
    assert tenant_b.org.clerk_org_id == "org_b"
    assert tenant_a.org.id != tenant_b.org.id


@pytest.mark.asyncio
async def test_personal_org_consistent(seeded_db, make_user):
    """Multiple calls without org_id return the same personal org."""
    user = make_user(user_id="bob")
    tenant1 = await resolve_tenant_context(user, seeded_db)
    tenant2 = await resolve_tenant_context(user, seeded_db)

    assert tenant1.org.id == tenant2.org.id
    assert tenant1.org.clerk_org_id.startswith(PERSONAL_ORG_PREFIX)

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

# pylint: disable=missing-function-docstring

"""Phase 2: Organization Repository Tests.

Tests OrgRepository CRUD and membership operations.
Requires PostgreSQL — skips if not available.
"""

import pytest

from apps.cruse.backend.db.repositories.org_repo import OrgRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


@pytest.mark.asyncio
async def test_upsert_creates_org(db):
    repo = OrgRepository(db)
    org = await repo.upsert_from_clerk("org_clerk1", "Test Org", slug="test-org")

    assert org.clerk_org_id == "org_clerk1"
    assert org.name == "Test Org"
    assert org.slug == "test-org"
    assert org.id is not None


@pytest.mark.asyncio
async def test_upsert_updates_existing(db):
    repo = OrgRepository(db)
    org1 = await repo.upsert_from_clerk("org_clerk2", "Original Name")
    org2 = await repo.upsert_from_clerk("org_clerk2", "Updated Name")

    assert org1.id == org2.id
    assert org2.name == "Updated Name"


@pytest.mark.asyncio
async def test_get_by_clerk_id(db):
    repo = OrgRepository(db)
    await repo.upsert_from_clerk("org_clerk3", "Find Me")
    await db.flush()

    found = await repo.get_by_clerk_id("org_clerk3")
    assert found is not None
    assert found.name == "Find Me"

    not_found = await repo.get_by_clerk_id("nonexistent")
    assert not_found is None


@pytest.mark.asyncio
async def test_upsert_membership(db):
    org_repo = OrgRepository(db)
    user_repo = UserRepository(db)

    await user_repo.upsert_from_clerk("alice", "alice@test.com", "Alice", "user")
    org = await org_repo.upsert_from_clerk("org_m1", "Membership Test")
    await db.flush()

    membership = await org_repo.upsert_membership(org.id, "alice", "admin")
    assert membership.org_id == org.id
    assert membership.user_id == "alice"
    assert membership.org_role == "admin"


@pytest.mark.asyncio
async def test_upsert_membership_idempotent(db):
    org_repo = OrgRepository(db)
    user_repo = UserRepository(db)

    await user_repo.upsert_from_clerk("bob", "bob@test.com", "Bob", "user")
    org = await org_repo.upsert_from_clerk("org_m2", "Idempotent Test")
    await db.flush()

    m1 = await org_repo.upsert_membership(org.id, "bob", "member")
    m2 = await org_repo.upsert_membership(org.id, "bob", "admin")

    assert m1.id == m2.id
    assert m2.org_role == "admin"


@pytest.mark.asyncio
async def test_list_for_user(db):
    org_repo = OrgRepository(db)
    user_repo = UserRepository(db)

    await user_repo.upsert_from_clerk("charlie", "charlie@test.com", "Charlie", "user")
    org_a = await org_repo.upsert_from_clerk("org_la", "Alpha Org")
    org_b = await org_repo.upsert_from_clerk("org_lb", "Beta Org")
    await db.flush()

    await org_repo.upsert_membership(org_a.id, "charlie", "member")
    await org_repo.upsert_membership(org_b.id, "charlie", "admin")
    await db.flush()

    orgs = await org_repo.list_for_user("charlie")
    org_names = {o.name for o in orgs}
    assert "Alpha Org" in org_names
    assert "Beta Org" in org_names


@pytest.mark.asyncio
async def test_list_for_user_empty(db):
    org_repo = OrgRepository(db)
    user_repo = UserRepository(db)
    await user_repo.upsert_from_clerk("lonely", "lonely@test.com", "Lonely", "user")
    await db.flush()

    orgs = await org_repo.list_for_user("lonely")
    assert orgs == []

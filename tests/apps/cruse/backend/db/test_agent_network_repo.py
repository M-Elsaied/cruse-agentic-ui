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

import pytest

from apps.cruse.backend.db.repositories.agent_network_repo import AgentNetworkRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository

HOCON = "{ llm_config { class_name = ChatOpenAI, model_name = gpt-4o-mini } tools = [] }"


async def _create_user(db, clerk_id="user1"):
    await UserRepository(db).upsert_from_clerk(clerk_id, f"{clerk_id}@test.com", clerk_id, "user")


@pytest.mark.asyncio
async def test_create(db):
    await _create_user(db)
    repo = AgentNetworkRepository(db)
    net = await repo.create("user1", "My Agent", "my_agent", HOCON)
    assert net.id is not None
    assert net.name == "My Agent"
    assert net.slug == "my_agent"
    assert net.is_shared is False
    assert net.is_archived is False


@pytest.mark.asyncio
async def test_duplicate_slug_same_user(db):
    await _create_user(db)
    repo = AgentNetworkRepository(db)
    await repo.create("user1", "Agent 1", "same_slug", HOCON)
    with pytest.raises(Exception):
        await repo.create("user1", "Agent 2", "same_slug", HOCON)


@pytest.mark.asyncio
async def test_same_slug_different_users(db):
    await _create_user(db, "user1")
    await _create_user(db, "user2")
    repo = AgentNetworkRepository(db)
    n1 = await repo.create("user1", "Agent", "shared_slug", HOCON)
    n2 = await repo.create("user2", "Agent", "shared_slug", HOCON)
    assert n1.id != n2.id


@pytest.mark.asyncio
async def test_list_owned(db):
    await _create_user(db)
    repo = AgentNetworkRepository(db)
    await repo.create("user1", "A", "a", HOCON)
    await repo.create("user1", "B", "b", HOCON)
    owned = await repo.list_owned("user1")
    assert len(owned) == 2


@pytest.mark.asyncio
async def test_list_shared(db):
    await _create_user(db, "user1")
    await _create_user(db, "user2")
    repo = AgentNetworkRepository(db)
    await repo.create("user1", "Shared", "shared", HOCON, org_id=None)
    # Not shared yet
    shared = await repo.list_shared("user2", 1)
    assert len(shared) == 0
    # Share it (need org_id to match)
    await repo.create("user1", "Org Shared", "org_shared", HOCON, org_id=1)
    await repo.update_metadata(
        (await repo.get_by_slug("user1", "org_shared")).id,
        is_shared=True,
    )
    shared = await repo.list_shared("user2", 1)
    assert len(shared) == 1
    assert shared[0].slug == "org_shared"


@pytest.mark.asyncio
async def test_update_content(db):
    await _create_user(db)
    repo = AgentNetworkRepository(db)
    net = await repo.create("user1", "Test", "test", HOCON)
    new_hocon = "{ llm_config { class_name = ChatAnthropic, model_name = claude-3 } tools = [] }"
    updated = await repo.update_content(net.id, new_hocon, name="Updated")
    assert updated is True
    fetched = await repo.get_by_id(net.id)
    assert fetched.hocon_content == new_hocon
    assert fetched.name == "Updated"


@pytest.mark.asyncio
async def test_archive(db):
    await _create_user(db)
    repo = AgentNetworkRepository(db)
    net = await repo.create("user1", "ToDelete", "to_delete", HOCON)
    archived = await repo.archive(net.id)
    assert archived is True
    assert await repo.get_by_id(net.id) is None
    assert await repo.count_for_user("user1") == 0


@pytest.mark.asyncio
async def test_count_for_user(db):
    await _create_user(db)
    repo = AgentNetworkRepository(db)
    assert await repo.count_for_user("user1") == 0
    await repo.create("user1", "A", "a", HOCON)
    await repo.create("user1", "B", "b", HOCON)
    assert await repo.count_for_user("user1") == 2


@pytest.mark.asyncio
async def test_is_accessible_owner(db):
    await _create_user(db)
    repo = AgentNetworkRepository(db)
    net = await repo.create("user1", "Test", "test", HOCON)
    assert await repo.is_accessible(net.id, "user1", None) is True
    assert await repo.is_accessible(net.id, "other_user", None) is False


@pytest.mark.asyncio
async def test_is_accessible_shared(db):
    await _create_user(db, "user1")
    await _create_user(db, "user2")
    repo = AgentNetworkRepository(db)
    net = await repo.create("user1", "Shared", "shared", HOCON, org_id=1)
    await repo.update_metadata(net.id, is_shared=True)
    # Same org can access
    assert await repo.is_accessible(net.id, "user2", 1) is True
    # Different org cannot
    assert await repo.is_accessible(net.id, "user2", 2) is False

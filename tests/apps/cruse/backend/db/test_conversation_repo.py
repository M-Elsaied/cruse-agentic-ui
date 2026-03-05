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

import pytest

from apps.cruse.backend.db.repositories.conversation_repo import ConversationRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


async def _create_user(db, clerk_id="user1"):
    await UserRepository(db).upsert_from_clerk(clerk_id, f"{clerk_id}@test.com", clerk_id, "user")


@pytest.mark.asyncio
async def test_create_conversation(db):
    await _create_user(db)
    repo = ConversationRepository(db)
    conv = await repo.create("sess-1", "user1", "test_network")
    assert conv.session_id == "sess-1"
    assert conv.user_id == "user1"
    assert conv.agent_network == "test_network"
    assert conv.is_archived is False


@pytest.mark.asyncio
async def test_list_conversations(db):
    await _create_user(db)
    repo = ConversationRepository(db)
    await repo.create("sess-1", "user1", "net1")
    await repo.create("sess-2", "user1", "net2")
    conversations = await repo.list("user1")
    assert len(conversations) == 2


@pytest.mark.asyncio
async def test_list_excludes_archived(db):
    await _create_user(db)
    repo = ConversationRepository(db)
    conv = await repo.create("sess-1", "user1", "net1")
    await repo.create("sess-2", "user1", "net2")
    await repo.archive(conv.id)
    conversations = await repo.list("user1")
    assert len(conversations) == 1


@pytest.mark.asyncio
async def test_list_includes_archived(db):
    await _create_user(db)
    repo = ConversationRepository(db)
    conv = await repo.create("sess-1", "user1", "net1")
    await repo.create("sess-2", "user1", "net2")
    await repo.archive(conv.id)
    conversations = await repo.list("user1", include_archived=True)
    assert len(conversations) == 2


@pytest.mark.asyncio
async def test_get_by_session_id(db):
    await _create_user(db)
    repo = ConversationRepository(db)
    await repo.create("sess-abc", "user1", "net1")
    found = await repo.get_by_session_id("sess-abc")
    assert found is not None
    assert found.agent_network == "net1"


@pytest.mark.asyncio
async def test_user_isolation(db):
    await _create_user(db, "userA")
    await _create_user(db, "userB")
    repo = ConversationRepository(db)
    await repo.create("s1", "userA", "net1")
    await repo.create("s2", "userB", "net1")
    result = await repo.list("userA")
    assert len(result) == 1
    assert result[0].user_id == "userA"


@pytest.mark.asyncio
async def test_update_title(db):
    await _create_user(db)
    repo = ConversationRepository(db)
    conv = await repo.create("sess-t", "user1", "net1")
    updated = await repo.update_title(conv.id, "My Chat Title")
    assert updated is True
    reloaded = await repo.get_by_id(conv.id)
    assert reloaded.title == "My Chat Title"

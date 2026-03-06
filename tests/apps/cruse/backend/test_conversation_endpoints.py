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

from apps.cruse.backend.db.repositories.conversation_repo import ConversationRepository
from apps.cruse.backend.db.repositories.message_repo import MessageRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


async def _ensure_user(db, user_id="user1"):
    await UserRepository(db).upsert_from_clerk(user_id, f"{user_id}@test.com", user_id, "user")


async def _create_conversation(db, user_id="user1", agent_network="basic/hello_world"):
    await _ensure_user(db, user_id)
    repo = ConversationRepository(db)
    conv = await repo.create(f"session-{user_id}", user_id, agent_network)
    await db.flush()
    return conv


@pytest.mark.asyncio
async def test_create_conversation(db):
    conv = await _create_conversation(db)
    assert conv.id is not None
    assert conv.session_id == "session-user1"
    assert conv.user_id == "user1"
    assert conv.agent_network == "basic/hello_world"
    assert conv.is_archived is False


@pytest.mark.asyncio
async def test_list_conversations_ordered(db):
    await _ensure_user(db)
    repo = ConversationRepository(db)
    conv1 = await repo.create("s1", "user1", "basic/hello_world")
    conv2 = await repo.create("s2", "user1", "basic/hello_world")
    await db.flush()

    convs = await repo.list("user1")
    assert len(convs) == 2
    # Most recent first
    assert convs[0].id == conv2.id
    assert convs[1].id == conv1.id


@pytest.mark.asyncio
async def test_get_conversation_with_messages(db):
    conv = await _create_conversation(db)
    msg_repo = MessageRepository(db)
    await msg_repo.append(conv.id, "user", "Hello")
    await msg_repo.append(conv.id, "assistant", "Hi there!")
    await db.flush()

    repo = ConversationRepository(db)
    loaded = await repo.get_with_messages(conv.id)
    assert loaded is not None
    assert len(loaded.messages) == 2
    assert loaded.messages[0].role == "user"
    assert loaded.messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_archive_conversation(db):
    conv = await _create_conversation(db)
    repo = ConversationRepository(db)

    result = await repo.archive(conv.id)
    assert result is True

    # Should not appear in default list
    convs = await repo.list("user1")
    assert len(convs) == 0

    # Should appear when include_archived=True
    convs = await repo.list("user1", include_archived=True)
    assert len(convs) == 1


@pytest.mark.asyncio
async def test_conversation_user_isolation(db):
    await _ensure_user(db, "user1")
    await _ensure_user(db, "user2")
    repo = ConversationRepository(db)
    await repo.create("s1", "user1", "basic/hello_world")
    await repo.create("s2", "user2", "basic/hello_world")
    await db.flush()

    user1_convs = await repo.list("user1")
    user2_convs = await repo.list("user2")
    assert len(user1_convs) == 1
    assert len(user2_convs) == 1
    assert user1_convs[0].user_id == "user1"
    assert user2_convs[0].user_id == "user2"


@pytest.mark.asyncio
async def test_update_title(db):
    conv = await _create_conversation(db)
    repo = ConversationRepository(db)

    result = await repo.update_title(conv.id, "My Chat")
    assert result is True

    loaded = await repo.get_by_id(conv.id)
    assert loaded is not None
    assert loaded.title == "My Chat"


@pytest.mark.asyncio
async def test_list_with_counts(db):
    await _ensure_user(db)
    repo = ConversationRepository(db)
    conv = await repo.create("s1", "user1", "basic/hello_world")
    await db.flush()

    msg_repo = MessageRepository(db)
    await msg_repo.append(conv.id, "user", "Hello")
    await msg_repo.append(conv.id, "assistant", "Hi!")
    await db.flush()

    rows = await repo.list_with_counts("user1")
    assert len(rows) == 1
    loaded_conv, msg_count = rows[0]
    assert loaded_conv.id == conv.id
    assert msg_count == 2


@pytest.mark.asyncio
async def test_list_with_counts_no_messages(db):
    await _ensure_user(db)
    repo = ConversationRepository(db)
    await repo.create("s1", "user1", "basic/hello_world")
    await db.flush()

    rows = await repo.list_with_counts("user1")
    assert len(rows) == 1
    _, msg_count = rows[0]
    assert msg_count == 0


@pytest.mark.asyncio
async def test_message_metadata(db):
    conv = await _create_conversation(db)
    msg_repo = MessageRepository(db)
    msg = await msg_repo.append(conv.id, "user", "Hello", metadata={"form_data": {"name": "test"}})
    await db.flush()

    assert msg.metadata_ is not None
    assert msg.metadata_["form_data"]["name"] == "test"


@pytest.mark.asyncio
async def test_get_by_session_id(db):
    conv = await _create_conversation(db)
    repo = ConversationRepository(db)

    loaded = await repo.get_by_session_id("session-user1")
    assert loaded is not None
    assert loaded.id == conv.id


@pytest.mark.asyncio
async def test_get_nonexistent_conversation(db):
    repo = ConversationRepository(db)
    loaded = await repo.get_by_id(99999)
    assert loaded is None

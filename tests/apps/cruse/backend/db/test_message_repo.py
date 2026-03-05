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
from apps.cruse.backend.db.repositories.message_repo import MessageRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


async def _create_conversation(db, session_id="sess-1"):
    await UserRepository(db).upsert_from_clerk("user1", "u@t.com", "U", "user")
    conv = await ConversationRepository(db).create(session_id, "user1", "net1")
    return conv


@pytest.mark.asyncio
async def test_append_message(db):
    conv = await _create_conversation(db)
    repo = MessageRepository(db)
    msg = await repo.append(conv.id, "user", "Hello world")
    assert msg.role == "user"
    assert msg.content == "Hello world"
    assert msg.metadata_ == {}


@pytest.mark.asyncio
async def test_append_with_metadata(db):
    conv = await _create_conversation(db)
    repo = MessageRepository(db)
    meta = {"widget_schema": {"type": "object"}, "tokens": {"prompt": 100}}
    msg = await repo.append(conv.id, "assistant", "Response", metadata=meta)
    assert msg.metadata_ == meta


@pytest.mark.asyncio
async def test_list_by_conversation_ordering(db):
    conv = await _create_conversation(db)
    repo = MessageRepository(db)
    await repo.append(conv.id, "user", "First")
    await repo.append(conv.id, "assistant", "Second")
    await repo.append(conv.id, "user", "Third")
    messages = await repo.list_by_conversation(conv.id)
    assert len(messages) == 3
    assert messages[0].content == "First"
    assert messages[2].content == "Third"


@pytest.mark.asyncio
async def test_list_with_pagination(db):
    conv = await _create_conversation(db)
    repo = MessageRepository(db)
    for i in range(10):
        await repo.append(conv.id, "user", f"Message {i}")
    page = await repo.list_by_conversation(conv.id, limit=3, offset=2)
    assert len(page) == 3
    assert page[0].content == "Message 2"


@pytest.mark.asyncio
async def test_large_content(db):
    conv = await _create_conversation(db)
    repo = MessageRepository(db)
    large_text = "x" * 50000
    msg = await repo.append(conv.id, "assistant", large_text)
    assert len(msg.content) == 50000

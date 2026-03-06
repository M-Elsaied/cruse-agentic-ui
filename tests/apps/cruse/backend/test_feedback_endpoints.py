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
from apps.cruse.backend.db.repositories.feedback_repo import FeedbackRepository
from apps.cruse.backend.db.repositories.message_repo import MessageRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


async def _setup_user(db, user_id="user1", role="user"):
    await UserRepository(db).upsert_from_clerk(user_id, f"{user_id}@test.com", user_id, role)


async def _setup_conversation_with_message(db, user_id="user1"):
    await _setup_user(db, user_id)
    conv = await ConversationRepository(db).create(f"session-{user_id}", user_id, "basic/hello_world")
    await db.flush()
    metadata = {"agent_trace": [{"agent": "test"}]}
    msg = await MessageRepository(db).append(conv.id, "assistant", "Hello!", metadata=metadata)
    await db.flush()
    return conv, msg


@pytest.mark.asyncio
async def test_post_rating_thumbs_up(db):
    _, msg = await _setup_conversation_with_message(db)
    repo = FeedbackRepository(db)
    fb = await repo.add_rating(msg.id, "user1", 1)
    await db.flush()

    assert fb.id is not None
    assert fb.rating == 1
    assert fb.comment is None


@pytest.mark.asyncio
async def test_post_rating_thumbs_down_with_comment(db):
    _, msg = await _setup_conversation_with_message(db)
    repo = FeedbackRepository(db)
    fb = await repo.add_rating(msg.id, "user1", -1, comment="Inaccurate response")
    await db.flush()

    assert fb.rating == -1
    assert fb.comment == "Inaccurate response"


@pytest.mark.asyncio
async def test_post_rating_upsert(db):
    _, msg = await _setup_conversation_with_message(db)
    repo = FeedbackRepository(db)

    fb1 = await repo.add_rating(msg.id, "user1", 1)
    await db.flush()
    assert fb1.rating == 1

    fb2 = await repo.add_rating(msg.id, "user1", -1, comment="Changed my mind")
    await db.flush()
    assert fb2.id == fb1.id  # Same row, upserted
    assert fb2.rating == -1
    assert fb2.comment == "Changed my mind"


@pytest.mark.asyncio
async def test_delete_rating(db):
    _, msg = await _setup_conversation_with_message(db)
    repo = FeedbackRepository(db)

    await repo.add_rating(msg.id, "user1", 1)
    await db.flush()

    deleted = await repo.delete_rating(msg.id, "user1")
    assert deleted is True


@pytest.mark.asyncio
async def test_delete_rating_nonexistent(db):
    _, msg = await _setup_conversation_with_message(db)
    repo = FeedbackRepository(db)

    deleted = await repo.delete_rating(msg.id, "user1")
    assert deleted is False


@pytest.mark.asyncio
async def test_post_report(db):
    await _setup_user(db)
    repo = FeedbackRepository(db)
    report = await repo.add_report("user1", "The agent gave wrong information", category="bug")
    await db.flush()

    assert report.id is not None
    assert report.category == "bug"
    assert report.status == "open"
    assert report.body == "The agent gave wrong information"


@pytest.mark.asyncio
async def test_post_report_with_message_context(db):
    conv, msg = await _setup_conversation_with_message(db)
    repo = FeedbackRepository(db)
    report = await repo.add_report(
        "user1",
        "Bug in response",
        category="bug",
        conversation_id=conv.id,
        message_id=msg.id,
        context={"agent_trace": [{"agent": "test"}], "agent_network": "basic/hello_world"},
    )
    await db.flush()

    assert report.conversation_id == conv.id
    assert report.message_id == msg.id
    assert report.context["agent_trace"] == [{"agent": "test"}]
    assert report.context["agent_network"] == "basic/hello_world"


@pytest.mark.asyncio
async def test_admin_list_reports(db):
    await _setup_user(db)
    repo = FeedbackRepository(db)
    await repo.add_report("user1", "Bug 1", category="bug")
    await repo.add_report("user1", "Feature idea", category="feature")
    await db.flush()

    reports = await repo.list_reports()
    assert len(reports) == 2

    count = await repo.count_reports()
    assert count == 2


@pytest.mark.asyncio
async def test_list_reports_filter_by_status(db):
    await _setup_user(db)
    repo = FeedbackRepository(db)
    await repo.add_report("user1", "Bug 1", category="bug")
    await repo.add_report("user1", "Bug 2", category="bug")
    await db.flush()

    open_reports = await repo.list_reports(status="open")
    assert len(open_reports) == 2

    resolved_reports = await repo.list_reports(status="resolved")
    assert len(resolved_reports) == 0

    open_count = await repo.count_reports(status="open")
    assert open_count == 2


@pytest.mark.asyncio
async def test_message_get_by_id(db):
    _, msg = await _setup_conversation_with_message(db)
    repo = MessageRepository(db)
    loaded = await repo.get_by_id(msg.id)
    assert loaded is not None
    assert loaded.id == msg.id
    assert loaded.content == "Hello!"


@pytest.mark.asyncio
async def test_message_get_by_id_nonexistent(db):
    repo = MessageRepository(db)
    loaded = await repo.get_by_id(99999)
    assert loaded is None

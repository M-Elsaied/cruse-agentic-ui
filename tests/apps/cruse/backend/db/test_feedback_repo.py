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
from apps.cruse.backend.db.repositories.feedback_repo import FeedbackRepository
from apps.cruse.backend.db.repositories.message_repo import MessageRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


async def _setup(db):
    await UserRepository(db).upsert_from_clerk("user1", "u@t.com", "U", "user")
    conv = await ConversationRepository(db).create("sess-fb", "user1", "net1")
    msg = await MessageRepository(db).append(conv.id, "assistant", "Hello")
    return conv, msg


@pytest.mark.asyncio
async def test_add_rating_thumbs_up(db):
    _, msg = await _setup(db)
    repo = FeedbackRepository(db)
    fb = await repo.add_rating(msg.id, "user1", 1)
    assert fb.rating == 1


@pytest.mark.asyncio
async def test_add_rating_thumbs_down(db):
    _, msg = await _setup(db)
    repo = FeedbackRepository(db)
    fb = await repo.add_rating(msg.id, "user1", -1, comment="Bad response")
    assert fb.rating == -1
    assert fb.comment == "Bad response"


@pytest.mark.asyncio
async def test_update_rating(db):
    _, msg = await _setup(db)
    repo = FeedbackRepository(db)
    await repo.add_rating(msg.id, "user1", 1)
    fb = await repo.add_rating(msg.id, "user1", -1)
    assert fb.rating == -1


@pytest.mark.asyncio
async def test_add_report(db):
    conv, _ = await _setup(db)
    repo = FeedbackRepository(db)
    report = await repo.add_report("user1", "Something went wrong", category="bug", conversation_id=conv.id)
    assert report.body == "Something went wrong"
    assert report.category == "bug"
    assert report.status == "open"


@pytest.mark.asyncio
async def test_list_reports(db):
    await _setup(db)
    repo = FeedbackRepository(db)
    await repo.add_report("user1", "Bug 1")
    await repo.add_report("user1", "Bug 2")
    reports = await repo.list_reports(user_id="user1")
    assert len(reports) == 2

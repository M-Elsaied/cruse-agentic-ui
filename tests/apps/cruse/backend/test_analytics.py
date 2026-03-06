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

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest

from apps.cruse.backend.db.repositories.conversation_repo import ConversationRepository
from apps.cruse.backend.db.repositories.feedback_repo import FeedbackRepository
from apps.cruse.backend.db.repositories.message_repo import MessageRepository
from apps.cruse.backend.db.repositories.request_log_repo import RequestLogRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


async def _setup_user(db, user_id="user1"):
    await UserRepository(db).upsert_from_clerk(user_id, f"{user_id}@test.com", user_id, "user")


async def _log_request(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    db, user_id="user1", network="basic/hello_world", latency_ms=1000, is_error=False, ago_days=0
):
    """Helper to create a request log entry, optionally backdated."""
    repo = RequestLogRepository(db)
    entry = await repo.log_request(user_id, network, latency_ms=latency_ms, is_error=is_error)
    if ago_days > 0:
        entry.created_at = datetime.now(tz=timezone.utc) - timedelta(days=ago_days)
        db.add(entry)
        await db.flush()
    return entry


# ─── RequestLogRepository.get_overview ────────────────────────


@pytest.mark.asyncio
async def test_get_overview_basic(db):
    await _setup_user(db)
    await _log_request(db, latency_ms=1000)
    await _log_request(db, latency_ms=2000)
    await _log_request(db, latency_ms=3000, is_error=True)
    await db.flush()

    result = await RequestLogRepository(db).get_overview(period_days=30)
    assert result["total_requests"] == 3
    assert result["unique_users"] == 1
    assert result["error_count"] == 1
    assert abs(result["error_rate"] - 1 / 3) < 0.01
    assert result["avg_latency_ms"] == 2000.0


@pytest.mark.asyncio
async def test_get_overview_period_comparison(db):
    await _setup_user(db)
    # Current period (within last 7 days)
    await _log_request(db, latency_ms=500, ago_days=1)
    await _log_request(db, latency_ms=500, ago_days=2)
    # Previous period (8-14 days ago)
    await _log_request(db, latency_ms=1000, ago_days=10)
    await db.flush()

    result = await RequestLogRepository(db).get_overview(period_days=7)
    assert result["total_requests"] == 2
    assert result["prev_total_requests"] == 1


@pytest.mark.asyncio
async def test_get_overview_empty(db):
    result = await RequestLogRepository(db).get_overview(period_days=30)
    assert result["total_requests"] == 0
    assert result["error_rate"] == 0.0
    assert result["avg_latency_ms"] == 0.0


# ─── RequestLogRepository.get_requests_over_time ──────────────


@pytest.mark.asyncio
async def test_get_requests_over_time(db):
    await _setup_user(db)
    await _log_request(db, ago_days=1)
    await _log_request(db, ago_days=1)
    await _log_request(db, ago_days=2, is_error=True)
    await db.flush()

    result = await RequestLogRepository(db).get_requests_over_time(period_days=7)
    assert len(result) >= 2
    total = sum(r["count"] for r in result)
    assert total == 3
    error_total = sum(r["error_count"] for r in result)
    assert error_total == 1


# ─── RequestLogRepository.get_active_users_over_time ──────────


@pytest.mark.asyncio
async def test_get_active_users_over_time(db):
    await _setup_user(db, "user1")
    await _setup_user(db, "user2")
    await _log_request(db, user_id="user1", ago_days=1)
    await _log_request(db, user_id="user2", ago_days=1)
    await _log_request(db, user_id="user1", ago_days=2)
    await db.flush()

    result = await RequestLogRepository(db).get_active_users_over_time(period_days=7)
    # Day with 2 users should show count=2
    day_counts = {r["date"]: r["count"] for r in result}
    assert any(c == 2 for c in day_counts.values())


# ─── RequestLogRepository.get_top_networks ────────────────────


@pytest.mark.asyncio
async def test_get_top_networks(db):
    await _setup_user(db)
    await _log_request(db, network="basic/hello_world")
    await _log_request(db, network="basic/hello_world")
    await _log_request(db, network="industry/insurance", is_error=True)
    await db.flush()

    result = await RequestLogRepository(db).get_top_networks(period_days=30)
    assert len(result) == 2
    assert result[0]["network"] == "basic/hello_world"
    assert result[0]["request_count"] == 2
    assert result[1]["network"] == "industry/insurance"
    assert result[1]["error_rate"] == 1.0


@pytest.mark.asyncio
async def test_get_top_networks_limit(db):
    await _setup_user(db)
    for i in range(5):
        await _log_request(db, network=f"net/{i}")
    await db.flush()

    result = await RequestLogRepository(db).get_top_networks(period_days=30, limit=3)
    assert len(result) == 3


# ─── RequestLogRepository.get_user_breakdown ──────────────────


@pytest.mark.asyncio
async def test_get_user_breakdown(db):
    await _setup_user(db, "user1")
    await _setup_user(db, "user2")
    await _log_request(db, user_id="user1")
    await _log_request(db, user_id="user1")
    await _log_request(db, user_id="user2")
    await db.flush()

    users, total = await RequestLogRepository(db).get_user_breakdown(period_days=30)
    assert total == 2
    assert len(users) == 2
    assert users[0]["request_count"] == 2  # user1 first (more requests)
    assert users[0]["email"] == "user1@test.com"


# ─── RequestLogRepository.get_export_rows ─────────────────────


@pytest.mark.asyncio
async def test_get_export_rows(db):
    await _setup_user(db)
    await _log_request(db, latency_ms=500)
    await _log_request(db, latency_ms=1000)
    await db.flush()

    rows = await RequestLogRepository(db).get_export_rows(period_days=30)
    assert len(rows) == 2
    assert "date" in rows[0]
    assert "agent_network" in rows[0]
    assert "latency_ms" in rows[0]


# ─── FeedbackRepository satisfaction ──────────────────────────


@pytest.mark.asyncio
async def test_get_satisfaction_score(db):
    await _setup_user(db)
    conv = await ConversationRepository(db).create("s1", "user1", "basic/hello_world")
    await db.flush()
    msg1 = await MessageRepository(db).append(conv.id, "assistant", "Hi")
    msg2 = await MessageRepository(db).append(conv.id, "assistant", "Hello")
    msg3 = await MessageRepository(db).append(conv.id, "assistant", "Hey")
    await db.flush()

    repo = FeedbackRepository(db)
    await repo.add_rating(msg1.id, "user1", 1)
    await repo.add_rating(msg2.id, "user1", 1)
    await repo.add_rating(msg3.id, "user1", -1)
    await db.flush()

    result = await repo.get_satisfaction_score(period_days=30)
    assert result["thumbs_up"] == 2
    assert result["thumbs_down"] == 1
    assert result["total"] == 3
    assert abs(result["score"] - 2 / 3) < 0.01


@pytest.mark.asyncio
async def test_get_network_satisfaction(db):
    await _setup_user(db)
    conv1 = await ConversationRepository(db).create("s1", "user1", "basic/hello_world")
    conv2 = await ConversationRepository(db).create("s2", "user1", "industry/insurance")
    await db.flush()
    msg1 = await MessageRepository(db).append(conv1.id, "assistant", "Hi")
    msg2 = await MessageRepository(db).append(conv2.id, "assistant", "Hello")
    await db.flush()

    repo = FeedbackRepository(db)
    await repo.add_rating(msg1.id, "user1", 1)
    await repo.add_rating(msg2.id, "user1", -1)
    await db.flush()

    result = await repo.get_network_satisfaction(period_days=30)
    by_net = {r["network"]: r for r in result}
    assert by_net["basic/hello_world"]["score"] == 1.0
    assert by_net["industry/insurance"]["score"] == 0.0


# ─── ConversationRepository.get_avg_depth_by_network ──────────


@pytest.mark.asyncio
async def test_get_avg_depth_by_network(db):
    await _setup_user(db)
    conv1 = await ConversationRepository(db).create("s1", "user1", "basic/hello_world")
    conv2 = await ConversationRepository(db).create("s2", "user1", "basic/hello_world")
    await db.flush()
    # conv1: 4 messages, conv2: 2 messages → avg = 3.0
    for _ in range(4):
        await MessageRepository(db).append(conv1.id, "assistant", "msg")
    for _ in range(2):
        await MessageRepository(db).append(conv2.id, "assistant", "msg")
    await db.flush()

    result = await ConversationRepository(db).get_avg_depth_by_network(period_days=30)
    assert len(result) == 1
    assert result[0]["network"] == "basic/hello_world"
    assert result[0]["avg_messages"] == 3.0
    assert result[0]["conversation_count"] == 2

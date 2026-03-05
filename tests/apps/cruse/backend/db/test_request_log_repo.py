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

from apps.cruse.backend.db.repositories.request_log_repo import RequestLogRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


async def _create_user(db, clerk_id="user1"):
    await UserRepository(db).upsert_from_clerk(clerk_id, f"{clerk_id}@test.com", clerk_id, "user")


@pytest.mark.asyncio
async def test_log_request(db):
    await _create_user(db)
    repo = RequestLogRepository(db)
    entry = await repo.log_request(
        "user1", "test_network", model="gpt-4o", prompt_tokens=100, completion_tokens=50, latency_ms=1200
    )
    assert entry.agent_network == "test_network"
    assert entry.prompt_tokens == 100


@pytest.mark.asyncio
async def test_get_stats(db):
    await _create_user(db)
    repo = RequestLogRepository(db)
    await repo.log_request("user1", "net1", prompt_tokens=100, completion_tokens=50, latency_ms=500)
    await repo.log_request("user1", "net1", prompt_tokens=200, completion_tokens=100, latency_ms=1000)
    stats = await repo.get_stats()
    assert stats["total_requests"] == 2
    assert stats["total_prompt_tokens"] == 300
    assert stats["total_completion_tokens"] == 150


@pytest.mark.asyncio
async def test_get_user_stats(db):
    await _create_user(db, "u1")
    await _create_user(db, "u2")
    repo = RequestLogRepository(db)
    await repo.log_request("u1", "net1", prompt_tokens=100)
    await repo.log_request("u2", "net1", prompt_tokens=200)
    stats = await repo.get_user_stats("u1")
    assert stats["total_requests"] == 1
    assert stats["total_prompt_tokens"] == 100


@pytest.mark.asyncio
async def test_get_stats_empty(db):
    stats = await RequestLogRepository(db).get_stats()
    assert stats["total_requests"] == 0
    assert stats["total_prompt_tokens"] == 0

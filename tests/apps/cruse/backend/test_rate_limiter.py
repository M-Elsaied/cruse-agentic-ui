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

import os

import pytest

from apps.cruse.backend.db.repositories.user_repo import UserRepository
from apps.cruse.backend.rate_limiter import RateLimiter

# These tests require the db/engine fixtures from
# tests/apps/cruse/backend/db/conftest.py (auto-discovered by pytest).


async def _create_user(db, clerk_id="user1"):
    await UserRepository(db).upsert_from_clerk(clerk_id, f"{clerk_id}@test.com", clerk_id, "user")


@pytest.fixture
def limiter():
    os.environ["MAX_DAILY_REQUESTS"] = "5"
    rl = RateLimiter()
    return rl


@pytest.mark.asyncio
async def test_check_and_increment(limiter, db):
    await limiter.init()
    await _create_user(db)
    allowed, remaining, limit = await limiter.check_and_increment("user1", "user", db)
    assert allowed is True
    assert remaining == 4
    assert limit == 5


@pytest.mark.asyncio
async def test_admin_bypass(limiter, db):
    await limiter.init()
    allowed, remaining, limit = await limiter.check_and_increment("admin1", "admin", db)
    assert allowed is True
    assert remaining is None
    assert limit is None


@pytest.mark.asyncio
async def test_rate_limit_enforced(limiter, db):
    await limiter.init()
    await _create_user(db)
    for _ in range(5):
        await limiter.check_and_increment("user1", "user", db)
    allowed, remaining, limit = await limiter.check_and_increment("user1", "user", db)
    assert allowed is False
    assert remaining == 0
    assert limit == 5


@pytest.mark.asyncio
async def test_get_remaining(limiter, db):
    await limiter.init()
    await _create_user(db)
    await limiter.check_and_increment("user1", "user", db)
    remaining, limit = await limiter.get_remaining("user1", "user", db)
    assert remaining == 4
    assert limit == 5


@pytest.mark.asyncio
async def test_get_remaining_admin(limiter, db):
    await limiter.init()
    remaining, limit = await limiter.get_remaining("admin1", "admin", db)
    assert remaining is None
    assert limit is None


@pytest.mark.asyncio
async def test_disabled(db):
    os.environ["MAX_DAILY_REQUESTS"] = "0"
    rl = RateLimiter()
    await rl.init()
    allowed, remaining, limit = await rl.check_and_increment("user1", "user", db)
    assert allowed is True
    assert remaining is None

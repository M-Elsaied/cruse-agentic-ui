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

from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pytest
from sqlalchemy import insert

from apps.cruse.backend.db.models import DailyUsage
from apps.cruse.backend.db.repositories.usage_repo import UsageRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


async def _create_user(db, clerk_id="user1"):
    await UserRepository(db).upsert_from_clerk(clerk_id, f"{clerk_id}@test.com", clerk_id, "user")


@pytest.mark.asyncio
async def test_increment_first_request(db):
    await _create_user(db)
    repo = UsageRepository(db)
    allowed, remaining = await repo.increment_and_check("user1", max_daily=5)
    assert allowed is True
    assert remaining == 4


@pytest.mark.asyncio
async def test_increment_multiple(db):
    await _create_user(db)
    repo = UsageRepository(db)
    await repo.increment_and_check("user1", max_daily=10)
    allowed, remaining = await repo.increment_and_check("user1", max_daily=10)
    assert allowed is True
    assert remaining == 8


@pytest.mark.asyncio
async def test_increment_at_limit(db):
    await _create_user(db)
    repo = UsageRepository(db)
    for _ in range(5):
        await repo.increment_and_check("user1", max_daily=5)
    allowed, remaining = await repo.increment_and_check("user1", max_daily=5)
    assert allowed is False
    assert remaining == 0


@pytest.mark.asyncio
async def test_exact_boundary(db):
    await _create_user(db)
    repo = UsageRepository(db)
    for i in range(4):
        allowed, remaining = await repo.increment_and_check("user1", max_daily=5)
        assert allowed is True
        assert remaining == 4 - i
    # 5th request — last allowed
    allowed, remaining = await repo.increment_and_check("user1", max_daily=5)
    assert allowed is True
    assert remaining == 0
    # 6th request — denied
    allowed, remaining = await repo.increment_and_check("user1", max_daily=5)
    assert allowed is False
    assert remaining == 0


@pytest.mark.asyncio
async def test_get_remaining_no_usage(db):
    await _create_user(db)
    repo = UsageRepository(db)
    remaining, limit = await repo.get_remaining("user1", max_daily=5)
    assert remaining == 5
    assert limit == 5


@pytest.mark.asyncio
async def test_get_remaining_after_usage(db):
    await _create_user(db)
    repo = UsageRepository(db)
    await repo.increment_and_check("user1", max_daily=5)
    await repo.increment_and_check("user1", max_daily=5)
    remaining, limit = await repo.get_remaining("user1", max_daily=5)
    assert remaining == 3
    assert limit == 5


@pytest.mark.asyncio
async def test_daily_reset(db):
    """Yesterday's usage should not affect today's count."""
    await _create_user(db)
    yesterday = (datetime.now(UTC) - timedelta(days=1)).date()
    await db.execute(insert(DailyUsage).values(user_id="user1", usage_date=yesterday, request_count=100))
    await db.flush()

    repo = UsageRepository(db)
    allowed, remaining = await repo.increment_and_check("user1", max_daily=5)
    assert allowed is True
    assert remaining == 4


@pytest.mark.asyncio
async def test_user_isolation(db):
    """Usage for one user should not affect another."""
    await _create_user(db, "user_a")
    await _create_user(db, "user_b")
    repo = UsageRepository(db)
    for _ in range(5):
        await repo.increment_and_check("user_a", max_daily=5)
    allowed, remaining = await repo.increment_and_check("user_b", max_daily=5)
    assert allowed is True
    assert remaining == 4

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

from apps.cruse.backend.db.repositories.user_repo import UserRepository


@pytest.mark.asyncio
async def test_upsert_creates_user(db):
    repo = UserRepository(db)
    user = await repo.upsert_from_clerk("clerk_1", "a@b.com", "Alice", "user")
    assert user.clerk_id == "clerk_1"
    assert user.email == "a@b.com"
    assert user.name == "Alice"
    assert user.role == "user"


@pytest.mark.asyncio
async def test_upsert_updates_existing(db):
    repo = UserRepository(db)
    await repo.upsert_from_clerk("clerk_2", "old@b.com", "Old Name", "user")
    updated = await repo.upsert_from_clerk("clerk_2", "new@b.com", "New Name", "admin")
    assert updated.email == "new@b.com"
    assert updated.name == "New Name"
    assert updated.role == "admin"


@pytest.mark.asyncio
async def test_get_by_id_found(db):
    repo = UserRepository(db)
    await repo.upsert_from_clerk("clerk_3", "c@d.com", "Bob", "user")
    found = await repo.get_by_id("clerk_3")
    assert found is not None
    assert found.email == "c@d.com"


@pytest.mark.asyncio
async def test_get_by_id_not_found(db):
    repo = UserRepository(db)
    assert await repo.get_by_id("nonexistent") is None


@pytest.mark.asyncio
async def test_upsert_with_null_email(db):
    repo = UserRepository(db)
    user = await repo.upsert_from_clerk("clerk_4", None, None, "user")
    assert user.email is None
    assert user.name is None
    assert user.role == "user"

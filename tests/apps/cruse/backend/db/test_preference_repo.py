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

from apps.cruse.backend.db.repositories.preference_repo import PreferenceRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


async def _create_user(db, clerk_id="user1"):
    await UserRepository(db).upsert_from_clerk(clerk_id, f"{clerk_id}@test.com", clerk_id, "user")


@pytest.mark.asyncio
async def test_get_returns_none_for_new_user(db):
    await _create_user(db)
    repo = PreferenceRepository(db)
    assert await repo.get("user1") is None


@pytest.mark.asyncio
async def test_update_creates_preference(db):
    await _create_user(db)
    repo = PreferenceRepository(db)
    pref = await repo.update("user1", preferred_provider="openai", preferred_model="gpt-4o")
    assert pref.preferred_provider == "openai"
    assert pref.preferred_model == "gpt-4o"


@pytest.mark.asyncio
async def test_update_partial(db):
    await _create_user(db)
    repo = PreferenceRepository(db)
    await repo.update("user1", preferred_provider="openai", preferred_model="gpt-4o")
    pref = await repo.update("user1", preferred_model="gpt-4o-mini")
    assert pref.preferred_model == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_jsonb_settings(db):
    await _create_user(db)
    repo = PreferenceRepository(db)
    settings = {"theme": "dark", "language": "en", "nested": {"key": "value"}}
    pref = await repo.update("user1", settings=settings)
    assert pref.settings == settings

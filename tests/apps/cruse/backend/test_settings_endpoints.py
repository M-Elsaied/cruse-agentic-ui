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

# pylint: disable=missing-function-docstring,redefined-outer-name

import os

import pytest

from apps.cruse.backend.db.encryption import reset_fernet
from apps.cruse.backend.db.repositories.api_key_repo import ApiKeyRepository
from apps.cruse.backend.db.repositories.preference_repo import PreferenceRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository
from apps.cruse.backend.key_resolver import has_any_valid_key
from apps.cruse.backend.rate_limiter import RateLimiter

# These tests require the db/engine fixtures from conftest.py


async def _create_user(db, clerk_id="user1"):
    await UserRepository(db).upsert_from_clerk(clerk_id, f"{clerk_id}@test.com", clerk_id, "user")


@pytest.fixture(autouse=True)
def _fernet_key():
    """Ensure a FERNET_KEY is available for encryption tests."""
    from cryptography.fernet import Fernet  # pylint: disable=import-outside-toplevel

    key = Fernet.generate_key().decode()
    os.environ["FERNET_KEY"] = key
    reset_fernet()
    yield
    reset_fernet()


# ─── API Key Repository Tests ────────────────────────────────────


@pytest.mark.asyncio
async def test_list_keys_empty(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    providers = await repo.list_providers("user1")
    assert providers == []


@pytest.mark.asyncio
async def test_store_key_success(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    api_key = await repo.store("user1", "openai", "sk-test1234abcd")
    assert api_key.provider == "openai"
    assert api_key.key_hint == "abcd"
    assert api_key.is_valid is True


@pytest.mark.asyncio
async def test_store_key_replaces_existing(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    await repo.store("user1", "openai", "sk-old-key-1111")
    api_key = await repo.store("user1", "openai", "sk-new-key-2222")
    assert api_key.key_hint == "2222"
    # Only one key per provider
    providers = await repo.list_providers("user1")
    assert len(providers) == 1


@pytest.mark.asyncio
async def test_delete_key_success(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    await repo.store("user1", "openai", "sk-test1234")
    deleted = await repo.delete("user1", "openai")
    assert deleted is True
    providers = await repo.list_providers("user1")
    assert len(providers) == 0


@pytest.mark.asyncio
async def test_delete_key_not_found(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    deleted = await repo.delete("user1", "openai")
    assert deleted is False


@pytest.mark.asyncio
async def test_keys_never_expose_raw(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    await repo.store("user1", "openai", "sk-secret-key-1234")
    providers = await repo.list_providers("user1")
    for p in providers:
        # The full key must never appear in list_providers output
        assert "sk-secret-key-1234" not in str(p)
        assert p["key_hint"] == "1234"


@pytest.mark.asyncio
async def test_list_keys_includes_hint(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    await repo.store("user1", "openai", "sk-test1234abcd", label="My key")
    providers = await repo.list_providers("user1")
    assert len(providers) == 1
    assert providers[0]["key_hint"] == "abcd"
    assert providers[0]["label"] == "My key"


# ─── Preference Repository Tests ─────────────────────────────────


@pytest.mark.asyncio
async def test_get_preferences_default(db):
    await _create_user(db)
    repo = PreferenceRepository(db)
    pref = await repo.get("user1")
    assert pref is None


@pytest.mark.asyncio
async def test_update_preferences(db):
    await _create_user(db)
    repo = PreferenceRepository(db)
    pref = await repo.update("user1", preferred_provider="openai", preferred_model="gpt-4o")
    assert pref.preferred_provider == "openai"
    assert pref.preferred_model == "gpt-4o"

    # Re-fetch
    fetched = await repo.get("user1")
    assert fetched is not None
    assert fetched.preferred_provider == "openai"


# ─── BYOK Rate Limit Bypass ──────────────────────────────────────


@pytest.mark.asyncio
async def test_byok_bypasses_rate_limit(db):
    os.environ["MAX_DAILY_REQUESTS"] = "5"
    rl = RateLimiter()
    await rl.init()
    await _create_user(db)
    allowed, remaining, limit = await rl.check_and_increment("user1", "user", db, has_byok=True)
    assert allowed is True
    assert remaining is None
    assert limit is None


@pytest.mark.asyncio
async def test_byok_get_remaining_bypass(db):
    os.environ["MAX_DAILY_REQUESTS"] = "5"
    rl = RateLimiter()
    await rl.init()
    await _create_user(db)
    remaining, limit = await rl.get_remaining("user1", "user", db, has_byok=True)
    assert remaining is None
    assert limit is None


# ─── BYOK Status Helpers ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_has_byok_false_without_keys(db):
    await _create_user(db)
    result = await has_any_valid_key("user1", db)
    assert result is False


@pytest.mark.asyncio
async def test_has_byok_true_with_keys(db):
    await _create_user(db)
    await ApiKeyRepository(db).store("user1", "openai", "sk-testkey")
    result = await has_any_valid_key("user1", db)
    assert result is True

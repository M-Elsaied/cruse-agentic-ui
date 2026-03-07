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

import os

import pytest

from apps.cruse.backend.db.encryption import reset_fernet
from apps.cruse.backend.db.repositories.api_key_repo import ApiKeyRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository
from apps.cruse.backend.key_resolver import has_any_valid_key
from apps.cruse.backend.key_resolver import resolve_keys

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


@pytest.mark.asyncio
async def test_has_any_key_false(db):
    await _create_user(db)
    result = await has_any_valid_key("user1", db)
    assert result is False


@pytest.mark.asyncio
async def test_has_any_key_true(db):
    await _create_user(db)
    await ApiKeyRepository(db).store("user1", "openai", "sk-test1234")
    result = await has_any_valid_key("user1", db)
    assert result is True


@pytest.mark.asyncio
async def test_resolve_keys_empty(db):
    await _create_user(db)
    keys = await resolve_keys("user1", db)
    assert keys == {}


@pytest.mark.asyncio
async def test_resolve_keys_returns_user_keys(db):
    await _create_user(db)
    await ApiKeyRepository(db).store("user1", "openai", "sk-test1234")
    keys = await resolve_keys("user1", db)
    assert "openai" in keys
    assert keys["openai"] == "sk-test1234"

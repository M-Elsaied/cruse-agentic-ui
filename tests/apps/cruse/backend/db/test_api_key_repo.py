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
from cryptography.fernet import Fernet

from apps.cruse.backend.db.encryption import reset_fernet
from apps.cruse.backend.db.repositories.api_key_repo import ApiKeyRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository


@pytest.fixture(autouse=True)
def _set_fernet_key():
    """Set a test FERNET_KEY for encryption."""
    key = Fernet.generate_key().decode()
    os.environ["FERNET_KEY"] = key
    reset_fernet()
    yield
    os.environ.pop("FERNET_KEY", None)
    reset_fernet()


async def _create_user(db, clerk_id="user1"):
    await UserRepository(db).upsert_from_clerk(clerk_id, f"{clerk_id}@test.com", clerk_id, "user")


@pytest.mark.asyncio
async def test_store_and_retrieve(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    await repo.store("user1", "openai", "sk-test-123")
    retrieved = await repo.retrieve("user1", "openai")
    assert retrieved == "sk-test-123"


@pytest.mark.asyncio
async def test_retrieve_nonexistent(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    assert await repo.retrieve("user1", "openai") is None


@pytest.mark.asyncio
async def test_store_replaces_existing(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    await repo.store("user1", "openai", "sk-old")
    await repo.store("user1", "openai", "sk-new")
    assert await repo.retrieve("user1", "openai") == "sk-new"


@pytest.mark.asyncio
async def test_list_providers(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    await repo.store("user1", "openai", "sk-1")
    await repo.store("user1", "anthropic", "sk-2")
    providers = await repo.list_providers("user1")
    provider_names = {p["provider"] for p in providers}
    assert provider_names == {"openai", "anthropic"}


@pytest.mark.asyncio
async def test_delete(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    await repo.store("user1", "openai", "sk-1")
    deleted = await repo.delete("user1", "openai")
    assert deleted is True
    assert await repo.retrieve("user1", "openai") is None


@pytest.mark.asyncio
async def test_delete_nonexistent(db):
    await _create_user(db)
    repo = ApiKeyRepository(db)
    deleted = await repo.delete("user1", "openai")
    assert deleted is False

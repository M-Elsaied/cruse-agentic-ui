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

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.encryption import decrypt_key
from apps.cruse.backend.db.encryption import encrypt_key
from apps.cruse.backend.db.models import ApiKey


class ApiKeyRepository:
    """Repository for encrypted BYOK API key management."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def store(self, user_id: str, provider: str, plaintext_key: str, *, label: str | None = None) -> ApiKey:
        """Encrypt and store an API key. Replaces existing key for the same provider."""
        encrypted = encrypt_key(plaintext_key)
        stmt = (
            insert(ApiKey)
            .values(
                user_id=user_id,
                provider=provider,
                encrypted_key=encrypted,
                label=label,
                is_valid=True,
            )
            .on_conflict_do_update(
                constraint="api_keys_user_id_provider_key",
                set_={
                    "encrypted_key": encrypted,
                    "label": label,
                    "is_valid": True,
                    "updated_at": func.now(),  # pylint: disable=not-callable
                },
            )
            .returning(ApiKey)
        )
        result = await self._db.execute(stmt)
        await self._db.flush()
        return result.scalar_one()

    async def retrieve(self, user_id: str, provider: str) -> str | None:
        """Retrieve and decrypt an API key. Returns None if not found."""
        result = await self._db.execute(
            select(ApiKey.encrypted_key).where(
                ApiKey.user_id == user_id,
                ApiKey.provider == provider,
                ApiKey.is_valid.is_(True),
            )
        )
        encrypted = result.scalar_one_or_none()
        if encrypted is None:
            return None
        return decrypt_key(encrypted)

    async def list_providers(self, user_id: str) -> list[dict]:
        """List all stored providers for a user (without exposing keys)."""
        result = await self._db.execute(
            select(ApiKey.provider, ApiKey.label, ApiKey.is_valid, ApiKey.created_at).where(ApiKey.user_id == user_id)
        )
        return [
            {"provider": row.provider, "label": row.label, "is_valid": row.is_valid, "created_at": row.created_at}
            for row in result.all()
        ]

    async def delete(self, user_id: str, provider: str) -> bool:
        """Delete an API key. Returns True if a key was deleted."""
        result = await self._db.execute(delete(ApiKey).where(ApiKey.user_id == user_id, ApiKey.provider == provider))
        await self._db.flush()
        return result.rowcount > 0

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

from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.db.repositories.api_key_repo import ApiKeyRepository

PROVIDER_ENV_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}

SUPPORTED_PROVIDERS: list[str] = list(PROVIDER_ENV_MAP.keys())


async def has_any_valid_key(user_id: str, db: AsyncSession) -> bool:
    """Check whether the user has at least one valid stored API key."""
    providers = await ApiKeyRepository(db).list_providers(user_id)
    return any(p["is_valid"] for p in providers)


async def resolve_keys(user_id: str, db: AsyncSession) -> dict[str, str]:
    """Resolve all stored keys for a user. Returns ``{provider: plaintext_key}``."""
    repo = ApiKeyRepository(db)
    result: dict[str, str] = {}
    for provider in SUPPORTED_PROVIDERS:
        key = await repo.retrieve(user_id, provider)
        if key:
            result[provider] = key
    return result

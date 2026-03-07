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

import logging

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0


async def validate_key(provider: str, key: str) -> tuple[bool, str]:
    """Validate an API key against the provider's API.

    Returns ``(is_valid, message)``.
    """
    logger.info("Validating %s key", provider)
    try:
        if provider == "openai":
            return await _validate_openai(key)
        if provider == "anthropic":
            return await _validate_anthropic(key)
        if provider == "google":
            return await _validate_google(key)
        return False, f"Unsupported provider: {provider}"
    except httpx.TimeoutException:
        return False, f"Validation timed out for {provider}"
    except httpx.HTTPError as exc:
        logger.warning("Network error validating %s key: %s", provider, exc)
        return False, f"Network error: could not reach {provider} API"


async def _validate_openai(key: str) -> tuple[bool, str]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {key}"},
        )
    if resp.status_code == 200:
        return True, "Valid OpenAI key"
    if resp.status_code == 401:
        return False, "Invalid OpenAI key"
    return False, f"Unexpected response from OpenAI: {resp.status_code}"


async def _validate_anthropic(key: str) -> tuple[bool, str]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            },
        )
    if resp.status_code in (200, 529):
        return True, "Valid Anthropic key"
    if resp.status_code == 401:
        return False, "Invalid Anthropic key"
    return False, f"Unexpected response from Anthropic: {resp.status_code}"


async def _validate_google(key: str) -> tuple[bool, str]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
    if resp.status_code == 200:
        return True, "Valid Google key"
    if resp.status_code in (400, 403):
        return False, "Invalid Google key"
    return False, f"Unexpected response from Google: {resp.status_code}"

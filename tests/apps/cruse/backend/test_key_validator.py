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

from unittest.mock import AsyncMock
from unittest.mock import patch

import httpx
import pytest

from apps.cruse.backend.key_validator import validate_key


def _mock_response(status_code: int):
    resp = AsyncMock(spec=httpx.Response)
    resp.status_code = status_code
    return resp


@pytest.mark.asyncio
async def test_validate_openai_valid():
    with patch("apps.cruse.backend.key_validator.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.get.return_value = _mock_response(200)
        mock_cls.return_value.__aenter__.return_value = client
        valid, msg = await validate_key("openai", "sk-test1234")
    assert valid is True
    assert "Valid" in msg


@pytest.mark.asyncio
async def test_validate_openai_invalid():
    with patch("apps.cruse.backend.key_validator.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.get.return_value = _mock_response(401)
        mock_cls.return_value.__aenter__.return_value = client
        valid, msg = await validate_key("openai", "sk-bad")
    assert valid is False
    assert "Invalid" in msg


@pytest.mark.asyncio
async def test_validate_anthropic_valid():
    with patch("apps.cruse.backend.key_validator.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.post.return_value = _mock_response(200)
        mock_cls.return_value.__aenter__.return_value = client
        valid, msg = await validate_key("anthropic", "sk-ant-test")
    assert valid is True


@pytest.mark.asyncio
async def test_validate_anthropic_invalid():
    with patch("apps.cruse.backend.key_validator.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.post.return_value = _mock_response(401)
        mock_cls.return_value.__aenter__.return_value = client
        valid, msg = await validate_key("anthropic", "sk-ant-bad")
    assert valid is False


@pytest.mark.asyncio
async def test_validate_google_valid():
    with patch("apps.cruse.backend.key_validator.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.get.return_value = _mock_response(200)
        mock_cls.return_value.__aenter__.return_value = client
        valid, msg = await validate_key("google", "AIza-test")
    assert valid is True


@pytest.mark.asyncio
async def test_validate_google_invalid():
    with patch("apps.cruse.backend.key_validator.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.get.return_value = _mock_response(400)
        mock_cls.return_value.__aenter__.return_value = client
        valid, msg = await validate_key("google", "AIza-bad")
    assert valid is False


@pytest.mark.asyncio
async def test_validate_unknown_provider():
    valid, msg = await validate_key("azure", "key123")
    assert valid is False
    assert "Unsupported" in msg


@pytest.mark.asyncio
async def test_validate_timeout():
    with patch("apps.cruse.backend.key_validator.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.get.side_effect = httpx.TimeoutException("timed out")
        mock_cls.return_value.__aenter__.return_value = client
        valid, msg = await validate_key("openai", "sk-test")
    assert valid is False
    assert "timed out" in msg


@pytest.mark.asyncio
async def test_validate_network_error():
    with patch("apps.cruse.backend.key_validator.httpx.AsyncClient") as mock_cls:
        client = AsyncMock()
        client.get.side_effect = httpx.ConnectError("connection refused")
        mock_cls.return_value.__aenter__.return_value = client
        valid, msg = await validate_key("openai", "sk-test")
    assert valid is False
    assert "Network error" in msg

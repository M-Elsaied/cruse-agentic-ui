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
import os
import time
from dataclasses import dataclass

import httpx
import jwt
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException

logger = logging.getLogger(__name__)

JWKS_CACHE_TTL = 3600  # 1 hour


@dataclass
class ClerkUser:
    """Represents an authenticated user extracted from a Clerk JWT."""

    user_id: str
    email: str | None
    role: str
    name: str | None


class ClerkJWTVerifier:
    """Verifies Clerk-issued JWTs using cached JWKS keys."""

    def __init__(self):
        self._jwks: dict = {}
        self._jwks_fetched_at: float = 0
        self._issuer: str | None = None

    async def init(self):
        """Fetch JWKS keys on startup."""
        await self._refresh_jwks()

    async def _refresh_jwks(self):
        """Fetch the JWKS key set from Clerk."""
        issuer = self._get_issuer()
        if not issuer:
            logger.warning("CLERK_ISSUER_URL not set, skipping JWKS fetch")
            return

        jwks_url = f"{issuer.rstrip('/')}/.well-known/jwks.json"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(jwks_url, timeout=10.0)
                resp.raise_for_status()
                self._jwks = resp.json()
                self._jwks_fetched_at = time.time()
                logger.info("JWKS keys fetched from %s", jwks_url)
        except Exception:
            logger.exception("Failed to fetch JWKS from %s", jwks_url)

    def _get_issuer(self) -> str | None:
        """Resolve the Clerk issuer URL from environment."""
        if self._issuer is None:
            self._issuer = os.environ.get("CLERK_ISSUER_URL", "")
        return self._issuer or None

    def _get_signing_key(self, kid: str):
        """Find the public key matching the given key ID."""
        for key in self._jwks.get("keys", []):
            if key.get("kid") == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(key)
        return None

    async def _ensure_jwks(self):
        """Refresh JWKS if cache has expired."""
        if time.time() - self._jwks_fetched_at > JWKS_CACHE_TTL:
            await self._refresh_jwks()

    async def verify_token(self, token: str) -> ClerkUser:
        """Verify a Clerk JWT and return the authenticated user.

        :param token: The raw JWT string from the Authorization header.
        :return: A ClerkUser with user_id, email, role, and name.
        :raises ValueError: If the token is invalid or verification fails.
        """
        await self._ensure_jwks()

        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.exceptions.DecodeError as exc:
            raise ValueError("Invalid token header") from exc

        kid = unverified_header.get("kid")
        if not kid:
            raise ValueError("Token missing key ID")

        signing_key = self._get_signing_key(kid)
        if signing_key is None:
            # Try refreshing JWKS once in case of key rotation
            await self._refresh_jwks()
            signing_key = self._get_signing_key(kid)
            if signing_key is None:
                raise ValueError("Unknown signing key")

        issuer = self._get_issuer()
        try:
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                issuer=issuer,
                options={"verify_aud": False},
            )
        except jwt.ExpiredSignatureError as exc:
            raise ValueError("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise ValueError(f"Invalid token: {exc}") from exc

        user_id = payload.get("sub", "")
        metadata = payload.get("metadata", {})
        if isinstance(metadata, str):
            metadata = {}

        return ClerkUser(
            user_id=user_id,
            email=metadata.get("email") or payload.get("email"),
            role=metadata.get("role", "user"),
            name=metadata.get("name") or payload.get("name"),
        )


# Module-level singleton
clerk_verifier = ClerkJWTVerifier()


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
) -> ClerkUser:
    """FastAPI dependency that extracts and verifies the Clerk JWT.

    Usage::

        @app.get("/api/endpoint")
        async def endpoint(user: ClerkUser = Depends(get_current_user)):
            ...
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        return await clerk_verifier.verify_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


async def require_admin(
    user: ClerkUser = Depends(get_current_user),
) -> ClerkUser:
    """FastAPI dependency that requires the authenticated user to be an admin."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def verify_ws_token(token: str) -> ClerkUser | None:
    """Verify a JWT for WebSocket connections.

    Returns None instead of raising so the caller can close
    the WebSocket with an appropriate code.
    """
    try:
        return await clerk_verifier.verify_token(token)
    except (ValueError, Exception):
        logger.debug("WebSocket token verification failed")
        return None

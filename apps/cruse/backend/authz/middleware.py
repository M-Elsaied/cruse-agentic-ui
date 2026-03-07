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

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException

from apps.cruse.backend.auth import ClerkUser

if TYPE_CHECKING:
    from apps.cruse.backend.authz.openfga_client import CruseOpenFGAClient

logger = logging.getLogger(__name__)


class AuthorizationService:
    """FastAPI-oriented authorization service backed by OpenFGA.

    Provides high-level permission checks that map to HTTP error responses.
    All authorization decisions flow through this service — no DB-based fallback.
    """

    def __init__(self, client: CruseOpenFGAClient):
        self._client = client

    async def require_org_permission(self, user: ClerkUser, org_id: str, permission: str = "read") -> None:
        """Verify a user has a permission on an organization.

        System admins (user.role == "admin") bypass this check.

        :param user: The authenticated user.
        :param org_id: The organization identifier.
        :param permission: The required relation (e.g. "read", "update", "create", "delete").
        :raises HTTPException: 403 if denied, 503 if OpenFGA is unavailable.
        """
        if user.role == "admin":
            return

        try:
            allowed = await self._client.check(user.user_id, permission, "Organization", org_id)
        except Exception as exc:
            logger.error("OpenFGA unavailable during org permission check: %s", exc)
            raise HTTPException(status_code=503, detail="Authorization service unavailable") from exc

        if not allowed:
            raise HTTPException(status_code=403, detail="Insufficient organization permissions")

    async def require_network_permission(self, user: ClerkUser, network_id: str, permission: str = "read") -> None:
        """Verify a user has a permission on an agent network.

        System admins (user.role == "admin") bypass this check.

        :param user: The authenticated user.
        :param network_id: The agent network identifier.
        :param permission: The required relation (e.g. "read", "update", "delete").
        :raises HTTPException: 403 if denied, 503 if OpenFGA is unavailable.
        """
        if user.role == "admin":
            return

        try:
            allowed = await self._client.check(user.user_id, permission, "AgentNetwork", network_id)
        except Exception as exc:
            logger.error("OpenFGA unavailable during network permission check: %s", exc)
            raise HTTPException(status_code=503, detail="Authorization service unavailable") from exc

        if not allowed:
            raise HTTPException(status_code=403, detail="Insufficient network permissions")

    async def list_accessible_networks(self, user: ClerkUser) -> list[str]:
        """List all agent network IDs the user can read.

        System admins get an empty list (they use unfiltered DB queries).

        :param user: The authenticated user.
        :return: List of network IDs the user has "read" access to.
        :raises HTTPException: 503 if OpenFGA is unavailable.
        """
        if user.role == "admin":
            return []

        try:
            return await self._client.list_objects(user.user_id, "read", "AgentNetwork")
        except Exception as exc:
            logger.error("OpenFGA unavailable during list_objects: %s", exc)
            raise HTTPException(status_code=503, detail="Authorization service unavailable") from exc

    async def check_org_permission(self, user: ClerkUser, org_id: str, permission: str = "read") -> bool:
        """Non-raising version of require_org_permission.

        :return: True if the user has the permission, False otherwise.
        :raises HTTPException: 503 if OpenFGA is unavailable.
        """
        if user.role == "admin":
            return True

        try:
            return await self._client.check(user.user_id, permission, "Organization", org_id)
        except Exception as exc:
            logger.error("OpenFGA unavailable: %s", exc)
            raise HTTPException(status_code=503, detail="Authorization service unavailable") from exc

    async def check_network_permission(self, user: ClerkUser, network_id: str, permission: str = "read") -> bool:
        """Non-raising version of require_network_permission.

        :return: True if the user has the permission, False otherwise.
        :raises HTTPException: 503 if OpenFGA is unavailable.
        """
        if user.role == "admin":
            return True

        try:
            return await self._client.check(user.user_id, permission, "AgentNetwork", network_id)
        except Exception as exc:
            logger.error("OpenFGA unavailable: %s", exc)
            raise HTTPException(status_code=503, detail="Authorization service unavailable") from exc

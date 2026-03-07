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

if TYPE_CHECKING:
    from apps.cruse.backend.authz.openfga_client import CruseOpenFGAClient

logger = logging.getLogger(__name__)


class TupleManager:
    """Centralized management of OpenFGA relationship tuples.

    Maps application events (org created, network created, etc.) to the
    corresponding tuple writes/deletes. This is the single place where
    tuple lifecycle logic lives — no other code should call grant/revoke
    directly on the OpenFGA client.
    """

    def __init__(self, client: CruseOpenFGAClient):
        self._client = client

    # ── Organization Events ──────────────────────────────────────

    async def on_org_created(self, org_id: str, creator_user_id: str) -> None:
        """When a new organization is created, the creator becomes admin."""
        await self._client.grant(f"User:{creator_user_id}", "admin", "Organization", org_id)
        logger.info("Tuple: User:%s is admin of Organization:%s", creator_user_id, org_id)

    async def on_user_joined_org(self, org_id: str, user_id: str) -> None:
        """When a user joins an organization, they become a member."""
        await self._client.grant(f"User:{user_id}", "member", "Organization", org_id)
        logger.info("Tuple: User:%s is member of Organization:%s", user_id, org_id)

    async def on_user_promoted_to_admin(self, org_id: str, user_id: str) -> None:
        """When a user is promoted to org admin."""
        await self._client.grant(f"User:{user_id}", "admin", "Organization", org_id)
        logger.info("Tuple: User:%s promoted to admin of Organization:%s", user_id, org_id)

    async def on_user_left_org(self, org_id: str, user_id: str) -> None:
        """When a user leaves an organization, remove their membership."""
        await self._client.revoke(f"User:{user_id}", "member", "Organization", org_id)
        await self._client.revoke(f"User:{user_id}", "admin", "Organization", org_id)
        logger.info("Tuple: User:%s removed from Organization:%s", user_id, org_id)

    async def on_org_deleted(self, org_id: str, member_user_ids: list[str]) -> None:
        """When an organization is deleted, remove all tuples referencing it.

        :param org_id: The organization being deleted.
        :param member_user_ids: All user IDs that were members of this org.
        """
        for user_id in member_user_ids:
            await self._client.revoke(f"User:{user_id}", "member", "Organization", org_id)
            await self._client.revoke(f"User:{user_id}", "admin", "Organization", org_id)
        logger.info("Tuple: All membership tuples removed for Organization:%s", org_id)

    # ── Agent Network Events ─────────────────────────────────────

    async def on_network_created(self, network_id: str, org_id: str, creator_user_id: str) -> None:
        """When a user creates a new agent network:
        1. Creator becomes owner
        2. Organization becomes container
        """
        await self._client.grant(f"User:{creator_user_id}", "owner", "AgentNetwork", network_id)
        await self._client.grant_org_relation(org_id, "container", "AgentNetwork", network_id)
        logger.info(
            "Tuple: User:%s owns AgentNetwork:%s in Organization:%s",
            creator_user_id,
            network_id,
            org_id,
        )

    async def on_network_deleted(self, network_id: str, org_id: str, owner_user_id: str) -> None:
        """When a network is deleted/archived, clean up its tuples."""
        await self._client.revoke(f"User:{owner_user_id}", "owner", "AgentNetwork", network_id)
        await self._client.revoke(f"Organization:{org_id}", "container", "AgentNetwork", network_id)
        logger.info("Tuple: AgentNetwork:%s tuples removed", network_id)

    async def on_network_shared(self, network_id: str, target_user_id: str, role: str = "collaborator") -> None:
        """When a network is shared with another user.

        :param role: One of "collaborator" or "tourist".
        """
        if role not in ("collaborator", "tourist"):
            raise ValueError(f"Invalid share role: {role}. Must be 'collaborator' or 'tourist'.")
        await self._client.grant(f"User:{target_user_id}", role, "AgentNetwork", network_id)
        logger.info("Tuple: User:%s is %s of AgentNetwork:%s", target_user_id, role, network_id)

    async def on_network_unshared(self, network_id: str, target_user_id: str, role: str = "collaborator") -> None:
        """When network sharing is revoked for a user."""
        if role not in ("collaborator", "tourist"):
            raise ValueError(f"Invalid share role: {role}. Must be 'collaborator' or 'tourist'.")
        await self._client.revoke(f"User:{target_user_id}", role, "AgentNetwork", network_id)
        logger.info("Tuple: User:%s no longer %s of AgentNetwork:%s", target_user_id, role, network_id)

    # ── Bootstrap ────────────────────────────────────────────────

    async def bootstrap_builtin_networks(self, network_names: list[str]) -> None:
        """Bootstrap tuples for built-in networks so all users can read them.

        Writes ``User:* tourist AgentNetwork:{name}`` for each built-in network.
        This uses the wildcard user syntax from the OpenFGA model.
        """
        for name in network_names:
            await self._client.grant("User:*", "tourist", "AgentNetwork", name)
        logger.info("Bootstrapped %d built-in network tuples", len(network_names))

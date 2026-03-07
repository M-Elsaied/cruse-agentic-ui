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

# pylint: disable=too-many-return-statements,too-many-branches,missing-function-docstring,too-many-arguments,too-many-positional-arguments

import pytest

from apps.cruse.backend.auth import ClerkUser


class MockOpenFGAClient:
    """In-memory OpenFGA mock for unit tests.

    Standalone mock that implements the same interface as CruseOpenFGAClient
    without importing openfga-sdk (which is not installed in CI).

    Stores tuples as a set of (user, relation, object_type, object_id) and
    implements the computed relations from the authorization model:
      - Organization: admin -> owner -> member (role hierarchy)
      - Organization: create/delete -> admin, read -> member, update -> owner
      - AgentNetwork: owner -> collaborator -> tourist (role hierarchy)
      - AgentNetwork: read -> tourist, update -> collaborator, delete/create -> owner
      - AgentNetwork: admin from container (org admin -> network owner)
    """

    def __init__(self):
        self._tuples: set[tuple[str, str, str, str]] = set()
        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def init(self) -> None:
        self._initialized = True

    async def close(self) -> None:
        self._initialized = False

    async def check(self, user_id: str, relation: str, object_type: str, object_id: str) -> bool:
        user = f"User:{user_id}"
        return self._check_internal(user, relation, object_type, object_id)

    def _check_internal(self, user: str, relation: str, object_type: str, object_id: str) -> bool:
        """Core check logic with computed relation expansion."""
        # Direct tuple match
        if (user, relation, object_type, object_id) in self._tuples:
            return True

        # Wildcard user match
        if ("User:*", relation, object_type, object_id) in self._tuples:
            return True

        # Computed relations for Organization
        if object_type == "Organization":
            return self._check_org_relation(user, relation, object_id)

        # Computed relations for AgentNetwork
        if object_type == "AgentNetwork":
            return self._check_network_relation(user, relation, object_id)

        return False

    def _check_org_relation(self, user: str, relation: str, org_id: str) -> bool:
        """Expand Organization computed relations (model hierarchy)."""
        # admin -> owner -> member
        if relation == "owner":
            return self._has_direct(user, "owner", "Organization", org_id) or self._has_direct(
                user, "admin", "Organization", org_id
            )
        if relation == "member":
            return self._has_direct(user, "member", "Organization", org_id) or self._check_org_relation(
                user, "owner", org_id
            )
        # Permissions
        if relation == "create":
            return self._check_org_relation(user, "admin", org_id)
        if relation == "delete":
            return self._check_org_relation(user, "admin", org_id)
        if relation == "read":
            return self._check_org_relation(user, "member", org_id)
        if relation == "update":
            return self._check_org_relation(user, "owner", org_id)
        # Direct only (admin)
        return self._has_direct(user, relation, "Organization", org_id)

    def _check_network_relation(self, user: str, relation: str, network_id: str) -> bool:
        """Expand AgentNetwork computed relations (model hierarchy)."""
        # owner: [User, Org#member] or admin from container
        if relation == "owner":
            if self._has_direct(user, "owner", "AgentNetwork", network_id):
                return True
            # admin from container: check if user is admin of the container org
            for t_user, t_rel, t_type, t_id in self._tuples:
                if t_rel == "container" and t_type == "AgentNetwork" and t_id == network_id:
                    container_org_id = t_user.split(":", 1)[1] if ":" in t_user else t_user
                    if self._check_org_relation(user, "admin", container_org_id):
                        return True
            return False

        # collaborator: [User, Org#member] or owner
        if relation == "collaborator":
            if self._has_direct(user, "collaborator", "AgentNetwork", network_id):
                return True
            return self._check_network_relation(user, "owner", network_id)

        # tourist: [User, User:*, Org#member] or collaborator
        if relation == "tourist":
            if self._has_direct(user, "tourist", "AgentNetwork", network_id):
                return True
            if ("User:*", "tourist", "AgentNetwork", network_id) in self._tuples:
                return True
            return self._check_network_relation(user, "collaborator", network_id)

        # Permissions
        if relation == "read":
            if self._has_direct(user, "read", "AgentNetwork", network_id):
                return True
            if ("User:*", "read", "AgentNetwork", network_id) in self._tuples:
                return True
            return self._check_network_relation(user, "tourist", network_id)
        if relation == "update":
            if self._has_direct(user, "update", "AgentNetwork", network_id):
                return True
            if ("User:*", "update", "AgentNetwork", network_id) in self._tuples:
                return True
            return self._check_network_relation(user, "collaborator", network_id)
        if relation == "create":
            if self._has_direct(user, "create", "AgentNetwork", network_id):
                return True
            if ("User:*", "create", "AgentNetwork", network_id) in self._tuples:
                return True
            return self._check_network_relation(user, "owner", network_id)
        if relation == "delete":
            if self._has_direct(user, "delete", "AgentNetwork", network_id):
                return True
            if ("User:*", "delete", "AgentNetwork", network_id) in self._tuples:
                return True
            return self._check_network_relation(user, "owner", network_id)

        return False

    def _has_direct(self, user: str, relation: str, object_type: str, object_id: str) -> bool:
        """Check for a direct (non-computed) tuple."""
        return (user, relation, object_type, object_id) in self._tuples

    async def grant(self, user: str, relation: str, object_type: str, object_id: str) -> bool:
        key = (user, relation, object_type, object_id)
        if key in self._tuples:
            return False
        self._tuples.add(key)
        return True

    async def revoke(self, user: str, relation: str, object_type: str, object_id: str) -> bool:
        key = (user, relation, object_type, object_id)
        if key not in self._tuples:
            return False
        self._tuples.discard(key)
        return True

    async def list_objects(self, user_id: str, relation: str, object_type: str) -> list[str]:
        user = f"User:{user_id}"
        result = set()
        # Collect all unique object IDs of the given type
        seen_ids = {t[3] for t in self._tuples if t[2] == object_type}
        for obj_id in seen_ids:
            if self._check_internal(user, relation, object_type, obj_id):
                result.add(obj_id)
        return sorted(result)

    async def grant_org_relation(self, org_id: str, relation: str, object_type: str, object_id: str) -> bool:
        return await self.grant(f"Organization:{org_id}", relation, object_type, object_id)

    async def grant_org_member_relation(self, org_id: str, relation: str, object_type: str, object_id: str) -> bool:
        return await self.grant(f"Organization:{org_id}#member", relation, object_type, object_id)


@pytest.fixture
def mock_openfga() -> MockOpenFGAClient:
    """Provide a fresh in-memory OpenFGA mock for each test."""
    return MockOpenFGAClient()


@pytest.fixture
def make_clerk_user():
    """Factory fixture: create ClerkUser instances for tests."""

    def _make(user_id="user1", role="user", email=None, name=None, org_id=None, org_role=None, org_slug=None):
        return ClerkUser(
            user_id=user_id,
            email=email or f"{user_id}@test.com",
            role=role,
            name=name or user_id,
            org_id=org_id,
            org_role=org_role,
            org_slug=org_slug,
        )

    return _make

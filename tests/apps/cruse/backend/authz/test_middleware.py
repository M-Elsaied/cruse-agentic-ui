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

"""Layer 3: Authorization Middleware Tests.

Tests the AuthorizationService using the MockOpenFGAClient to verify
that FastAPI authorization dependencies correctly allow/deny access.
"""

import pytest
from fastapi import HTTPException

from apps.cruse.backend.authz.middleware import AuthorizationService
from apps.cruse.backend.authz.tuple_manager import TupleManager


@pytest.fixture
def authz(mock_openfga):
    return AuthorizationService(mock_openfga)


@pytest.fixture
def tuple_mgr(mock_openfga):
    return TupleManager(mock_openfga)


@pytest.mark.asyncio
async def test_require_org_permission_granted(authz, mock_openfga, make_clerk_user):
    user = make_clerk_user(user_id="alice")
    await mock_openfga.grant("User:alice", "member", "Organization", "org1")
    # Should not raise
    await authz.require_org_permission(user, "org1", "read")


@pytest.mark.asyncio
async def test_require_org_permission_denied(authz, make_clerk_user):
    user = make_clerk_user(user_id="alice")
    with pytest.raises(HTTPException) as exc_info:
        await authz.require_org_permission(user, "org1", "read")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_network_read_granted(authz, mock_openfga, make_clerk_user):
    user = make_clerk_user(user_id="alice")
    await mock_openfga.grant("User:alice", "tourist", "AgentNetwork", "net1")
    await authz.require_network_permission(user, "net1", "read")


@pytest.mark.asyncio
async def test_require_network_update_denied_for_tourist(authz, mock_openfga, make_clerk_user):
    user = make_clerk_user(user_id="alice")
    await mock_openfga.grant("User:alice", "tourist", "AgentNetwork", "net1")
    with pytest.raises(HTTPException) as exc_info:
        await authz.require_network_permission(user, "net1", "update")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_network_delete_denied_for_collaborator(authz, mock_openfga, make_clerk_user):
    user = make_clerk_user(user_id="alice")
    await mock_openfga.grant("User:alice", "collaborator", "AgentNetwork", "net1")
    with pytest.raises(HTTPException) as exc_info:
        await authz.require_network_permission(user, "net1", "delete")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_network_delete_granted_for_owner(authz, mock_openfga, make_clerk_user):
    user = make_clerk_user(user_id="alice")
    await mock_openfga.grant("User:alice", "owner", "AgentNetwork", "net1")
    await authz.require_network_permission(user, "net1", "delete")


@pytest.mark.asyncio
async def test_system_admin_bypasses_org_check(authz, make_clerk_user):
    admin = make_clerk_user(user_id="admin1", role="admin")
    # Admin should pass without any tuples
    await authz.require_org_permission(admin, "any_org", "delete")


@pytest.mark.asyncio
async def test_system_admin_bypasses_network_check(authz, make_clerk_user):
    admin = make_clerk_user(user_id="admin1", role="admin")
    await authz.require_network_permission(admin, "any_network", "delete")


@pytest.mark.asyncio
async def test_org_admin_can_create_network(authz, mock_openfga, make_clerk_user):
    """Org admin has 'create' permission on the org (not on the network directly)."""
    user = make_clerk_user(user_id="alice")
    await mock_openfga.grant("User:alice", "admin", "Organization", "org1")
    await authz.require_org_permission(user, "org1", "create")


@pytest.mark.asyncio
async def test_org_member_cannot_create_in_org(authz, mock_openfga, make_clerk_user):
    """Regular member cannot create (admin permission required)."""
    user = make_clerk_user(user_id="bob")
    await mock_openfga.grant("User:bob", "member", "Organization", "org1")
    with pytest.raises(HTTPException) as exc_info:
        await authz.require_org_permission(user, "org1", "create")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_cross_org_access_denied(authz, mock_openfga, make_clerk_user, tuple_mgr):
    """User in org_a cannot access org_b's network."""
    user_a = make_clerk_user(user_id="alice")
    await tuple_mgr.on_org_created("org_a", "alice")
    await tuple_mgr.on_org_created("org_b", "bob")
    await tuple_mgr.on_network_created("net_b", "org_b", "bob")

    with pytest.raises(HTTPException) as exc_info:
        await authz.require_network_permission(user_a, "net_b", "read")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_list_accessible_networks(authz, mock_openfga, make_clerk_user):
    user = make_clerk_user(user_id="alice")
    await mock_openfga.grant("User:alice", "owner", "AgentNetwork", "my_net")
    await mock_openfga.grant("User:*", "tourist", "AgentNetwork", "builtin_net")
    result = await authz.list_accessible_networks(user)
    assert "my_net" in result
    assert "builtin_net" in result


@pytest.mark.asyncio
async def test_list_accessible_networks_admin_returns_empty(authz, make_clerk_user):
    """System admins get empty list (they use unfiltered DB queries)."""
    admin = make_clerk_user(user_id="admin1", role="admin")
    result = await authz.list_accessible_networks(admin)
    assert result == []


@pytest.mark.asyncio
async def test_check_org_permission_non_raising(authz, mock_openfga, make_clerk_user):
    user = make_clerk_user(user_id="alice")
    await mock_openfga.grant("User:alice", "member", "Organization", "org1")
    assert await authz.check_org_permission(user, "org1", "read") is True
    assert await authz.check_org_permission(user, "org1", "create") is False

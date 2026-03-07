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

# pylint: disable=missing-function-docstring,protected-access

"""Layer 1: OpenFGA Client Unit Tests.

Tests the core authorization operations using the MockOpenFGAClient
which simulates the OpenFGA authorization model in-memory.
"""

import pytest


@pytest.mark.asyncio
async def test_check_granted_returns_true(mock_openfga):
    await mock_openfga.grant("User:alice", "member", "Organization", "org1")
    assert await mock_openfga.check("alice", "member", "Organization", "org1") is True


@pytest.mark.asyncio
async def test_check_denied_returns_false(mock_openfga):
    assert await mock_openfga.check("alice", "member", "Organization", "org1") is False


@pytest.mark.asyncio
async def test_grant_writes_tuple(mock_openfga):
    result = await mock_openfga.grant("User:alice", "member", "Organization", "org1")
    assert result is True
    assert ("User:alice", "member", "Organization", "org1") in mock_openfga._tuples


@pytest.mark.asyncio
async def test_grant_idempotent(mock_openfga):
    first = await mock_openfga.grant("User:alice", "member", "Organization", "org1")
    second = await mock_openfga.grant("User:alice", "member", "Organization", "org1")
    assert first is True
    assert second is False  # Already existed


@pytest.mark.asyncio
async def test_revoke_deletes_tuple(mock_openfga):
    await mock_openfga.grant("User:alice", "member", "Organization", "org1")
    result = await mock_openfga.revoke("User:alice", "member", "Organization", "org1")
    assert result is True
    assert ("User:alice", "member", "Organization", "org1") not in mock_openfga._tuples


@pytest.mark.asyncio
async def test_revoke_nonexistent_returns_false(mock_openfga):
    result = await mock_openfga.revoke("User:alice", "member", "Organization", "org1")
    assert result is False


@pytest.mark.asyncio
async def test_check_after_revoke_returns_false(mock_openfga):
    await mock_openfga.grant("User:alice", "member", "Organization", "org1")
    await mock_openfga.revoke("User:alice", "member", "Organization", "org1")
    assert await mock_openfga.check("alice", "member", "Organization", "org1") is False


@pytest.mark.asyncio
async def test_list_objects_returns_accessible(mock_openfga):
    await mock_openfga.grant("User:alice", "owner", "AgentNetwork", "net1")
    await mock_openfga.grant("User:alice", "tourist", "AgentNetwork", "net2")
    result = await mock_openfga.list_objects("alice", "read", "AgentNetwork")
    assert "net1" in result
    assert "net2" in result


@pytest.mark.asyncio
async def test_list_objects_empty_for_no_access(mock_openfga):
    await mock_openfga.grant("User:bob", "owner", "AgentNetwork", "net1")
    result = await mock_openfga.list_objects("alice", "read", "AgentNetwork")
    assert result == []


@pytest.mark.asyncio
async def test_wildcard_user_access(mock_openfga):
    await mock_openfga.grant("User:*", "tourist", "AgentNetwork", "hello_world")
    assert await mock_openfga.check("alice", "read", "AgentNetwork", "hello_world") is True
    assert await mock_openfga.check("bob", "read", "AgentNetwork", "hello_world") is True


@pytest.mark.asyncio
async def test_org_member_inherits_read(mock_openfga):
    """admin -> owner -> member, and member has 'read' permission."""
    await mock_openfga.grant("User:alice", "admin", "Organization", "org1")
    assert await mock_openfga.check("alice", "read", "Organization", "org1") is True


@pytest.mark.asyncio
async def test_org_admin_inherits_owner_and_member(mock_openfga):
    """admin implies owner implies member."""
    await mock_openfga.grant("User:alice", "admin", "Organization", "org1")
    assert await mock_openfga.check("alice", "owner", "Organization", "org1") is True
    assert await mock_openfga.check("alice", "member", "Organization", "org1") is True


@pytest.mark.asyncio
async def test_collaborator_can_update(mock_openfga):
    await mock_openfga.grant("User:alice", "collaborator", "AgentNetwork", "net1")
    assert await mock_openfga.check("alice", "update", "AgentNetwork", "net1") is True


@pytest.mark.asyncio
async def test_tourist_cannot_update(mock_openfga):
    await mock_openfga.grant("User:alice", "tourist", "AgentNetwork", "net1")
    assert await mock_openfga.check("alice", "update", "AgentNetwork", "net1") is False


@pytest.mark.asyncio
async def test_owner_can_delete(mock_openfga):
    await mock_openfga.grant("User:alice", "owner", "AgentNetwork", "net1")
    assert await mock_openfga.check("alice", "delete", "AgentNetwork", "net1") is True


@pytest.mark.asyncio
async def test_member_cannot_delete_network(mock_openfga):
    """A member of the org (not owner/collaborator of the network) cannot delete it."""
    await mock_openfga.grant("User:alice", "member", "Organization", "org1")
    await mock_openfga.grant("Organization:org1", "container", "AgentNetwork", "net1")
    # alice is a member of the org but not an admin — so she's NOT owner of the network
    assert await mock_openfga.check("alice", "delete", "AgentNetwork", "net1") is False


@pytest.mark.asyncio
async def test_org_admin_inherits_network_owner_via_container(mock_openfga):
    """Org admin becomes network owner via the container relation."""
    await mock_openfga.grant("User:alice", "admin", "Organization", "org1")
    await mock_openfga.grant("Organization:org1", "container", "AgentNetwork", "net1")
    assert await mock_openfga.check("alice", "owner", "AgentNetwork", "net1") is True
    assert await mock_openfga.check("alice", "read", "AgentNetwork", "net1") is True
    assert await mock_openfga.check("alice", "delete", "AgentNetwork", "net1") is True

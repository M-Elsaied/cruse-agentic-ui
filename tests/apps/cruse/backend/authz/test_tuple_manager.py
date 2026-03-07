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

# pylint: disable=missing-function-docstring,redefined-outer-name,protected-access

"""Layer 2: Tuple Manager Unit Tests.

Tests the TupleManager's event-to-tuple mapping logic using the MockOpenFGAClient.
"""

import pytest

from apps.cruse.backend.authz.tuple_manager import TupleManager


@pytest.fixture
def tuple_manager(mock_openfga):
    return TupleManager(mock_openfga)


@pytest.mark.asyncio
async def test_on_org_created_writes_admin_tuple(tuple_manager, mock_openfga):
    await tuple_manager.on_org_created("org1", "alice")
    assert ("User:alice", "admin", "Organization", "org1") in mock_openfga._tuples


@pytest.mark.asyncio
async def test_on_user_joined_writes_member_tuple(tuple_manager, mock_openfga):
    await tuple_manager.on_user_joined_org("org1", "bob")
    assert ("User:bob", "member", "Organization", "org1") in mock_openfga._tuples


@pytest.mark.asyncio
async def test_on_user_promoted_writes_admin_tuple(tuple_manager, mock_openfga):
    await tuple_manager.on_user_joined_org("org1", "bob")
    await tuple_manager.on_user_promoted_to_admin("org1", "bob")
    assert ("User:bob", "admin", "Organization", "org1") in mock_openfga._tuples


@pytest.mark.asyncio
async def test_on_network_created_writes_owner_and_container(tuple_manager, mock_openfga):
    await tuple_manager.on_network_created("net1", "org1", "alice")
    assert ("User:alice", "owner", "AgentNetwork", "net1") in mock_openfga._tuples
    assert ("Organization:org1", "container", "AgentNetwork", "net1") in mock_openfga._tuples


@pytest.mark.asyncio
async def test_on_network_deleted_removes_tuples(tuple_manager, mock_openfga):
    await tuple_manager.on_network_created("net1", "org1", "alice")
    await tuple_manager.on_network_deleted("net1", "org1", "alice")
    assert ("User:alice", "owner", "AgentNetwork", "net1") not in mock_openfga._tuples
    assert ("Organization:org1", "container", "AgentNetwork", "net1") not in mock_openfga._tuples


@pytest.mark.asyncio
async def test_bootstrap_builtin_networks(tuple_manager, mock_openfga):
    networks = ["hello_world", "math_tutor", "travel_agent"]
    await tuple_manager.bootstrap_builtin_networks(networks)
    for name in networks:
        assert ("User:*", "tourist", "AgentNetwork", name) in mock_openfga._tuples


@pytest.mark.asyncio
async def test_idempotent_tuple_write(tuple_manager, mock_openfga):
    """Double-writing the same event should not error."""
    await tuple_manager.on_org_created("org1", "alice")
    await tuple_manager.on_org_created("org1", "alice")
    assert ("User:alice", "admin", "Organization", "org1") in mock_openfga._tuples


@pytest.mark.asyncio
async def test_on_network_shared_writes_collaborator(tuple_manager, mock_openfga):
    await tuple_manager.on_network_shared("net1", "bob", role="collaborator")
    assert ("User:bob", "collaborator", "AgentNetwork", "net1") in mock_openfga._tuples


@pytest.mark.asyncio
async def test_on_network_unshared_removes_collaborator(tuple_manager, mock_openfga):
    await tuple_manager.on_network_shared("net1", "bob", role="collaborator")
    await tuple_manager.on_network_unshared("net1", "bob", role="collaborator")
    assert ("User:bob", "collaborator", "AgentNetwork", "net1") not in mock_openfga._tuples


@pytest.mark.asyncio
async def test_on_network_shared_invalid_role_raises(tuple_manager):
    with pytest.raises(ValueError, match="Invalid share role"):
        await tuple_manager.on_network_shared("net1", "bob", role="admin")


@pytest.mark.asyncio
async def test_on_org_deleted_removes_all_tuples(tuple_manager, mock_openfga):
    await tuple_manager.on_org_created("org1", "alice")
    await tuple_manager.on_user_joined_org("org1", "bob")
    await tuple_manager.on_org_deleted("org1", ["alice", "bob"])
    assert ("User:alice", "admin", "Organization", "org1") not in mock_openfga._tuples
    assert ("User:bob", "member", "Organization", "org1") not in mock_openfga._tuples


@pytest.mark.asyncio
async def test_on_user_left_org_removes_membership(tuple_manager, mock_openfga):
    await tuple_manager.on_user_joined_org("org1", "bob")
    await tuple_manager.on_user_left_org("org1", "bob")
    assert ("User:bob", "member", "Organization", "org1") not in mock_openfga._tuples

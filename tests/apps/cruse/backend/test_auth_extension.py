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

"""Phase 2: Auth Extension Tests.

Tests that ClerkUser correctly carries org claims and that
the _normalize_org_role helper works.
"""

from apps.cruse.backend.auth import ClerkUser
from apps.cruse.backend.tenant_context import _normalize_org_role


def test_clerk_user_has_org_fields():
    user = ClerkUser(
        user_id="u1",
        email="u1@test.com",
        role="user",
        name="User One",
        org_id="org_123",
        org_role="org:admin",
        org_slug="my-org",
    )
    assert user.org_id == "org_123"
    assert user.org_role == "org:admin"
    assert user.org_slug == "my-org"


def test_clerk_user_org_fields_default_none():
    user = ClerkUser(user_id="u2", email="u2@test.com", role="user", name="User Two")
    assert user.org_id is None
    assert user.org_role is None
    assert user.org_slug is None


def test_normalize_org_role_admin():
    assert _normalize_org_role("org:admin") == "admin"


def test_normalize_org_role_member():
    assert _normalize_org_role("org:member") == "member"


def test_normalize_org_role_owner():
    assert _normalize_org_role("org:owner") == "owner"


def test_normalize_org_role_none():
    assert _normalize_org_role(None) == "member"


def test_normalize_org_role_empty():
    assert _normalize_org_role("") == "member"


def test_normalize_org_role_unknown():
    assert _normalize_org_role("org:viewer") == "member"

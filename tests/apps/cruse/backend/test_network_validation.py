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

from apps.cruse.backend.network_validator import validate_hocon
from apps.cruse.backend.network_validator import validate_slug


def test_valid_hocon():
    errors = validate_hocon('{ key = "value" }')
    assert not errors


def test_invalid_hocon_syntax():
    errors = validate_hocon("{ key = [}")
    assert len(errors) == 1
    assert "Invalid HOCON syntax" in errors[0]


def test_include_rejected():
    errors = validate_hocon('include "some_file.hocon"\n{ key = "value" }')
    assert len(errors) == 1
    assert "include" in errors[0].lower()


def test_empty_content():
    errors = validate_hocon("")
    assert len(errors) == 1
    assert "required" in errors[0].lower()


def test_valid_slug():
    assert not validate_slug("my_agent_42")


def test_invalid_slug_uppercase():
    errors = validate_slug("MyAgent")
    assert len(errors) == 1


def test_invalid_slug_spaces():
    errors = validate_slug("my agent")
    assert len(errors) == 1


def test_empty_slug():
    errors = validate_slug("")
    assert len(errors) == 1

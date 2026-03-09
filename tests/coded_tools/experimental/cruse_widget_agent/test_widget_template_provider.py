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

"""Unit tests for WidgetTemplateProvider coded tool.

Tests the sly_data-based widget session context that enables
the LLM to avoid generating duplicate widgets.
"""

import json

import pytest

from coded_tools.experimental.cruse_widget_agent.widget_template_provider import WidgetTemplateProvider


@pytest.fixture
def provider():
    """Create a WidgetTemplateProvider instance."""
    return WidgetTemplateProvider()


class TestWidgetTemplateProvider:  # pylint: disable=redefined-outer-name
    """Tests for WidgetTemplateProvider.invoke()."""

    def test_template_request_returns_template(self, provider):
        """request_type=template returns only the template."""
        result = json.loads(provider.invoke({"request_type": "template"}, {}))
        assert "template" in result
        assert "widget_type_examples" not in result

    def test_examples_request_returns_examples(self, provider):
        """request_type=examples returns only the examples."""
        result = json.loads(provider.invoke({"request_type": "examples"}, {}))
        assert "widget_type_examples" in result
        assert "template" not in result

    def test_full_request_returns_all_sections(self, provider):
        """request_type=full returns template, examples, icons, instructions, and session_context."""
        result = json.loads(provider.invoke({"request_type": "full"}, {}))
        assert "template" in result
        assert "widget_type_examples" in result
        assert "icon_guidance" in result
        assert "instructions" in result
        assert "session_context" in result

    def test_session_context_empty_sly_data(self, provider):
        """Empty sly_data yields empty-default session context."""
        result = json.loads(provider.invoke({"request_type": "full"}, {}))
        ctx = result["session_context"]
        assert ctx["previously_submitted"] == {}
        assert ctx["fields_already_collected"] == []
        assert ctx["last_widget_fields"] == []
        assert ctx["widget_count_this_session"] == 0

    def test_session_context_with_submitted_fields(self, provider):
        """sly_data with widget_state surfaces previously submitted data."""
        sly_data = {
            "widget_state": {
                "submitted_fields": ["checkInDate", "checkOutDate", "budget"],
                "submission_data": {"checkInDate": "2026-03-09", "checkOutDate": "2026-03-10", "budget": 250},
                "last_widget_fields": ["checkInDate", "checkOutDate", "budget", "preferences"],
                "widget_count": 1,
            }
        }
        result = json.loads(provider.invoke({"request_type": "full"}, sly_data))
        ctx = result["session_context"]
        assert ctx["previously_submitted"]["checkInDate"] == "2026-03-09"
        assert ctx["previously_submitted"]["budget"] == 250
        assert "checkInDate" in ctx["fields_already_collected"]
        assert ctx["last_widget_fields"] == ["checkInDate", "checkOutDate", "budget", "preferences"]
        assert ctx["widget_count_this_session"] == 1

    def test_session_context_included_in_non_full_requests(self, provider):
        """session_context is included even for template-only requests."""
        sly_data = {"widget_state": {"submission_data": {"name": "Alice"}}}
        result = json.loads(provider.invoke({"request_type": "template"}, sly_data))
        assert "session_context" in result
        assert result["session_context"]["previously_submitted"]["name"] == "Alice"

    def test_widget_count_incremented_in_sly_data(self, provider):
        """Each invocation increments widget_count in sly_data."""
        sly_data = {}
        provider.invoke({"request_type": "full"}, sly_data)
        assert sly_data["widget_state"]["widget_count"] == 1

        provider.invoke({"request_type": "full"}, sly_data)
        assert sly_data["widget_state"]["widget_count"] == 2

    def test_widget_count_preserves_existing_state(self, provider):
        """Incrementing widget_count does not overwrite other widget_state keys."""
        sly_data = {
            "widget_state": {
                "submitted_fields": ["email"],
                "widget_count": 3,
            }
        }
        provider.invoke({"request_type": "full"}, sly_data)
        assert sly_data["widget_state"]["widget_count"] == 4
        assert sly_data["widget_state"]["submitted_fields"] == ["email"]

    def test_sly_data_other_keys_untouched(self, provider):
        """Provider does not modify unrelated sly_data keys."""
        sly_data = {"selected_agent": "registries/foo.hocon", "agent_session": "mock_session"}
        provider.invoke({"request_type": "full"}, sly_data)
        assert sly_data["selected_agent"] == "registries/foo.hocon"
        assert sly_data["agent_session"] == "mock_session"

    def test_default_request_type_is_full(self, provider):
        """Omitting request_type defaults to full."""
        result = json.loads(provider.invoke({}, {}))
        assert "template" in result
        assert "instructions" in result
        assert "session_context" in result

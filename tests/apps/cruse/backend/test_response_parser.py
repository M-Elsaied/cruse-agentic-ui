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

"""Unit tests for apps.cruse.backend.response_parser."""

from apps.cruse.backend.response_parser import parse_response_blocks
from apps.cruse.backend.response_parser import try_parse_json


class TestTryParseJson:  # pylint: disable=missing-function-docstring
    """Tests for try_parse_json()."""

    def test_valid_json_object(self):
        assert try_parse_json('{"title": "Hello"}') == {"title": "Hello"}

    def test_valid_json_array(self):
        assert try_parse_json("[1, 2, 3]") == [1, 2, 3]

    def test_invalid_json_returns_none(self):
        assert try_parse_json("not json at all") is None

    def test_strips_markdown_json_fence(self):
        content = '```json\n{"display": false}\n```'
        assert try_parse_json(content) == {"display": False}

    def test_strips_markdown_bare_fence(self):
        content = '```\n{"key": "value"}\n```'
        assert try_parse_json(content) == {"key": "value"}

    def test_fence_with_invalid_json_returns_none(self):
        content = "```json\nnot valid json\n```"
        assert try_parse_json(content) is None

    def test_empty_string_returns_none(self):
        assert try_parse_json("") is None

    def test_none_returns_none(self):
        assert try_parse_json(None) is None


class TestParseResponseBlocks:  # pylint: disable=missing-function-docstring
    """Tests for parse_response_blocks()."""

    def test_say_only(self):
        blocks = parse_response_blocks("say: Hello, how can I help?")
        assert len(blocks) == 1
        assert blocks[0] == ("say", "Hello, how can I help?")

    def test_say_with_multiline(self):
        response = "say: Line 1\nLine 2\nLine 3"
        blocks = parse_response_blocks(response)
        assert len(blocks) == 1
        assert blocks[0][0] == "say"
        assert "Line 1" in blocks[0][1]
        assert "Line 3" in blocks[0][1]

    def test_say_and_gui_json(self):
        response = 'say: Here is a form\ngui: {"title": "Test", "schema": {}}'
        blocks = parse_response_blocks(response)
        assert len(blocks) == 2
        assert blocks[0] == ("say", "Here is a form")
        assert blocks[1][0] == "gui_json"
        assert blocks[1][1]["title"] == "Test"

    def test_gui_display_false(self):
        response = 'say: No widget needed\ngui: {"display": false}'
        blocks = parse_response_blocks(response)
        assert len(blocks) == 2
        assert blocks[1][0] == "gui_json"
        assert blocks[1][1]["display"] is False

    def test_gui_invalid_json_becomes_gui_html(self):
        response = "say: Here\ngui: <div>Some HTML</div>"
        blocks = parse_response_blocks(response)
        assert len(blocks) == 2
        assert blocks[1][0] == "gui_html"
        assert "<div>" in blocks[1][1]

    def test_gui_with_markdown_fences(self):
        response = 'say: Fill this out\ngui: ```json\n{"title": "Form"}\n```'
        blocks = parse_response_blocks(response)
        assert len(blocks) == 2
        assert blocks[1][0] == "gui_json"
        assert blocks[1][1]["title"] == "Form"

    def test_no_prefix_fallback(self):
        """Response without say:/gui: prefixes treated as single say block."""
        blocks = parse_response_blocks("Just a plain response with no prefix")
        assert len(blocks) == 1
        assert blocks[0] == ("say", "Just a plain response with no prefix")

    def test_empty_response(self):
        blocks = parse_response_blocks("")
        assert len(blocks) == 0

    def test_whitespace_only_response(self):
        blocks = parse_response_blocks("   \n  \n  ")
        assert len(blocks) == 0

    def test_multiple_gui_blocks(self):
        response = 'gui: {"title": "A"}\ngui: {"title": "B"}'
        blocks = parse_response_blocks(response)
        assert len(blocks) == 2
        assert blocks[0][1]["title"] == "A"
        assert blocks[1][1]["title"] == "B"

    def test_case_insensitive_prefix(self):
        """Prefixes are matched case-insensitively."""
        response = 'Say: Hello\nGUI: {"display": false}'
        blocks = parse_response_blocks(response)
        assert len(blocks) == 2
        assert blocks[0][0] == "say"
        assert blocks[1][0] == "gui_json"

    def test_multiline_gui_json(self):
        """Multi-line gui: JSON block is parsed correctly."""
        response = 'say: Here\ngui: {\n  "title": "Multi",\n  "schema": {}\n}'
        blocks = parse_response_blocks(response)
        assert len(blocks) == 2
        assert blocks[1][0] == "gui_json"
        assert blocks[1][1]["title"] == "Multi"

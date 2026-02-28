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

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def try_parse_json(content: str) -> Any:
    """Attempt to parse a string as JSON.

    Tries the raw content first, then strips markdown code fences
    (```json ... ```) which LLMs sometimes wrap around JSON output.

    :param content: The string to attempt JSON parsing on.
    :return: Parsed JSON object if successful, None otherwise.
    """
    # Try raw content first
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try stripping markdown code fences
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        # Remove first line (```json or ```) and last line (```)
        if len(lines) >= 3 and lines[-1].strip() == "```":
            inner = "\n".join(lines[1:-1])
            try:
                return json.loads(inner)
            except (json.JSONDecodeError, TypeError):
                pass

    return None


def parse_response_blocks(response: str) -> list[tuple[str, Any]]:
    """Parse a multiline response string into structured content blocks.

    Enhanced version of the original cruse_assistant.parse_response_blocks()
    that also attempts to parse gui: blocks as JSON (for widget schemas).

    :param response: The raw response string to parse.
    :return: A list of (block_type, content) tuples where block_type is
             'say', 'gui_json', or 'gui_html', and content is the
             corresponding parsed data.
    """
    blocks = []
    current_type = None
    current_lines = []

    for line in response.splitlines():
        line = line.rstrip()

        if line.lower().startswith("say:"):
            if current_type:
                blocks.append((current_type, "\n".join(current_lines).strip()))
            current_type = "say"
            current_lines = [line[4:].lstrip()]
        elif line.lower().startswith("gui:"):
            if current_type:
                blocks.append((current_type, "\n".join(current_lines).strip()))
            current_type = "gui"
            current_lines = [line[4:].lstrip()]
        else:
            current_lines.append(line)

    if current_type and current_lines:
        blocks.append((current_type, "\n".join(current_lines).strip()))

    # Post-process: try to parse gui blocks as JSON
    result = []
    for kind, content in blocks:
        if not content:
            continue
        if kind == "gui":
            parsed = try_parse_json(content)
            if parsed is not None:
                result.append(("gui_json", parsed))
            else:
                result.append(("gui_html", content))
        else:
            result.append((kind, content))

    # Fallback: if no blocks matched, treat the whole response as a say block
    if not result and response.strip():
        result.append(("say", response.strip()))

    return result

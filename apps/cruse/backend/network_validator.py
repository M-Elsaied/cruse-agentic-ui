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

import re

from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigException

MAX_HOCON_SIZE_BYTES = 500 * 1024  # 500 KB
SLUG_PATTERN = re.compile(r"^[a-z0-9_]+$")


def validate_slug(slug: str) -> list[str]:
    """Validate a network slug."""
    errors: list[str] = []
    if not slug:
        errors.append("Slug is required.")
    elif not SLUG_PATTERN.match(slug):
        errors.append("Slug must contain only lowercase letters, digits, and underscores.")
    elif len(slug) > 255:
        errors.append("Slug must be 255 characters or fewer.")
    return errors


def validate_hocon(hocon_content: str) -> list[str]:
    """Validate HOCON content for syntax, security, and size.

    :return: List of error messages (empty = valid).
    """
    errors: list[str] = []

    if not hocon_content or not hocon_content.strip():
        errors.append("HOCON content is required.")
        return errors

    if len(hocon_content.encode("utf-8")) > MAX_HOCON_SIZE_BYTES:
        errors.append(f"HOCON content exceeds maximum size of {MAX_HOCON_SIZE_BYTES // 1024} KB.")
        return errors

    # Security: reject include directives (could read arbitrary files)
    if _has_include_directive(hocon_content):
        errors.append("HOCON 'include' directives are not allowed in custom networks.")
        return errors

    # Parse HOCON — resolve=False allows ${aaosa_instructions} etc. which are
    # provided by includes injected at materialization time, not in user content.
    try:
        ConfigFactory.parse_string(hocon_content, resolve=False)
    except (ConfigException, Exception) as exc:  # pylint: disable=broad-exception-caught
        errors.append(f"Invalid HOCON syntax: {exc}")

    return errors


def _has_include_directive(content: str) -> bool:
    """Check if HOCON content contains include directives.

    Looks for 'include' at the start of a line (ignoring whitespace),
    but not inside strings or comments.
    """
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("#"):
            continue
        if re.match(r"^\s*include\s", line):
            return True
    return False

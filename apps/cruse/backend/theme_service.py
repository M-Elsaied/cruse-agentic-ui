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

import logging
import os
from typing import Any

from pyhocon import ConfigFactory

logger = logging.getLogger(__name__)

# Import CSS_DOODLE_TEMPLATES once at module level instead of per-call.
try:
    from coded_tools.experimental.cruse_theme_agent.cruse_theme_constants import CSS_DOODLE_TEMPLATES
except ImportError:
    logger.warning("CSS_DOODLE_TEMPLATES not available — theme matching disabled")
    CSS_DOODLE_TEMPLATES = {}

# Default fallback gradient
DEFAULT_THEME = {
    "type": "gradient",
    "mode": "linear",
    "angle": "135deg",
    "colors": [
        {"color": "#0f172a", "stop": "0%"},
        {"color": "#1e293b", "stop": "100%"},
    ],
    "description": "Default dark gradient",
}

# Simple tag-based theme selection (static mapping, no need to rebuild per call)
_TAG_THEME_MAP = {
    "finance": "financial_grid",
    "banking": "financial_grid",
    "airline": "aviation_flow",
    "travel": "aviation_flow",
    "health": "organic_dots",
    "medical": "organic_dots",
    "education": "educational_blocks",
    "creative": "creative_chaos",
    "technology": "geometric_tech",
    "ai": "neural_network",
}

# Cache metadata reads — HOCON files don't change at runtime.
_metadata_cache: dict[str, dict[str, Any] | None] = {}


def _read_agent_metadata(agent_network: str) -> dict[str, Any] | None:
    """Read metadata block from an agent network HOCON file.

    Results are cached since HOCON files don't change at runtime.

    :param agent_network: The relative HOCON path (e.g. 'basic/airline_policy.hocon').
    :return: Dict with metadata if found, None otherwise.
    """
    if agent_network in _metadata_cache:
        return _metadata_cache[agent_network]

    hocon_name = agent_network if agent_network.endswith(".hocon") else f"{agent_network}.hocon"
    hocon_path = os.path.join("registries", hocon_name)
    if not os.path.exists(hocon_path):
        _metadata_cache[agent_network] = None
        return None

    try:
        # Parse without resolving substitutions — HOCON files use includes
        # and ${variables} that fail when parsed standalone (include paths
        # are relative to the file, not CWD). We only need the metadata block.
        config = ConfigFactory.parse_file(hocon_path, resolve=False)
        metadata = config.get("metadata", None)
        result = dict(metadata) if metadata else None
        _metadata_cache[agent_network] = result
        return result
    except Exception:
        logger.exception("Failed to read metadata from %s", hocon_path)
        _metadata_cache[agent_network] = None
        return None


def get_sample_queries_for_network(agent_network: str) -> list[str]:
    """Get sample queries from an agent network's metadata.

    :param agent_network: The agent network HOCON path.
    :return: List of sample query strings, empty if none found.
    """
    metadata = _read_agent_metadata(agent_network)
    if not metadata:
        return []
    return list(metadata.get("sample_queries", []))


def get_theme_for_network(agent_network: str) -> dict[str, Any]:
    """Get a theme definition for a given agent network.

    Synchronous — no need for asyncio since metadata reads are cached.

    :param agent_network: The agent network HOCON path.
    :return: A theme definition dict.
    """
    metadata = _read_agent_metadata(agent_network)

    if not metadata:
        return DEFAULT_THEME

    # Extract tags for theme matching
    tags = metadata.get("tags", [])
    description = metadata.get("description", "")

    for tag in tags:
        tag_lower = tag.lower()
        for keyword, template_name in _TAG_THEME_MAP.items():
            if keyword in tag_lower:
                template = CSS_DOODLE_TEMPLATES.get(template_name)
                if template:
                    return dict(template)

    # Check description for keywords
    desc_lower = description.lower()
    for keyword, template_name in _TAG_THEME_MAP.items():
        if keyword in desc_lower:
            template = CSS_DOODLE_TEMPLATES.get(template_name)
            if template:
                return dict(template)

    return DEFAULT_THEME

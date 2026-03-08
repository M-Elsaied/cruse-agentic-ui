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

from apps.cruse.backend.db.engine import get_session_factory
from apps.cruse.backend.db.models import AgentNetwork
from apps.cruse.backend.db.repositories.agent_network_repo import AgentNetworkRepository

logger = logging.getLogger(__name__)

REGISTRIES_DIR = "registries"
GENERATED_DIR = os.path.join(REGISTRIES_DIR, "generated")
GENERATED_MANIFEST = os.path.join(GENERATED_DIR, "manifest.hocon")


def _network_filename(created_by: str, slug: str) -> str:
    """Build the HOCON filename for a user network.

    Format: {user_short_id}_{slug}.hocon
    user_short_id = first 8 chars after 'user_' prefix (or first 8 of raw id).
    """
    user_short = created_by.replace("user_", "")[:8]
    return f"{user_short}_{slug}.hocon"


def _network_path(created_by: str, slug: str) -> str:
    """Full path to the network's HOCON file."""
    return os.path.join(GENERATED_DIR, _network_filename(created_by, slug))


def network_key(created_by: str, slug: str) -> str:
    """The manifest key / network name for a user network.

    Format: generated/{user_short_id}_{slug}
    This matches the pattern used by neuro-san manifest includes.
    """
    user_short = created_by.replace("user_", "")[:8]
    return f"generated/{user_short}_{slug}"


def ensure_generated_dir() -> None:
    """Ensure the generated directory and its manifest exist."""
    os.makedirs(GENERATED_DIR, exist_ok=True)
    if not os.path.exists(GENERATED_MANIFEST):
        with open(GENERATED_MANIFEST, "w", encoding="utf-8") as fh:
            fh.write("{\n}\n")
        logger.info("Created empty generated manifest at %s", GENERATED_MANIFEST)


def materialize(network: AgentNetwork) -> str:
    """Write a network's HOCON content to disk and register in the generated manifest.

    :param network: The AgentNetwork DB record.
    :return: The filesystem path of the written file.
    """
    ensure_generated_dir()

    file_path = _network_path(network.created_by, network.slug)
    with open(file_path, "w", encoding="utf-8") as fh:
        # Prepend standard includes so custom networks can use ${aaosa_instructions},
        # ${aaosa_call}, ${aaosa_command}, and inherit the platform llm_config.
        # The user's HOCON is stored without includes (blocked by validator for security),
        # but the materialized file gets them injected server-side.
        fh.write('include "../aaosa_basic.hocon"\n')
        fh.write('include "../llm_config.hocon"\n\n')
        fh.write(network.hocon_content)
    logger.info("Materialized network %s -> %s", network.slug, file_path)

    _register_in_manifest(network.created_by, network.slug)
    return file_path


def dematerialize(created_by: str, slug: str) -> None:
    """Remove a network's HOCON file from disk and unregister from the manifest."""
    file_path = _network_path(created_by, slug)
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info("Removed materialized file %s", file_path)

    _unregister_from_manifest(created_by, slug)


def materialize_all(networks: list[AgentNetwork]) -> int:
    """Materialize all active networks from DB to disk. Used at startup.

    :return: Number of networks materialized.
    """
    ensure_generated_dir()
    count = 0
    for net in networks:
        materialize(net)
        count += 1
    logger.info("Materialized %d custom networks at startup", count)
    return count


def _register_in_manifest(created_by: str, slug: str) -> None:
    """Add a network entry to the generated manifest if not already present."""
    key = network_key(created_by, slug)
    filename = _network_filename(created_by, slug)

    with open(GENERATED_MANIFEST, "r", encoding="utf-8") as fh:
        content = fh.read()

    if filename in content:
        return

    entry = f'    "{key}.hocon": true,'
    insert_pos = content.rfind("}")
    if insert_pos != -1:
        updated = content[:insert_pos] + "\n" + entry + "\n" + content[insert_pos:]
    else:
        updated = content.rstrip() + "\n" + f'"{key}.hocon" = true\n'

    with open(GENERATED_MANIFEST, "w", encoding="utf-8") as fh:
        fh.write(updated)
    logger.debug("Registered %s in generated manifest", key)


def _unregister_from_manifest(created_by: str, slug: str) -> None:
    """Remove a network entry from the generated manifest."""
    key = network_key(created_by, slug)
    filename = _network_filename(created_by, slug)

    if not os.path.exists(GENERATED_MANIFEST):
        return

    with open(GENERATED_MANIFEST, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    filtered = [line for line in lines if filename not in line and key not in line]

    with open(GENERATED_MANIFEST, "w", encoding="utf-8") as fh:
        fh.writelines(filtered)
    logger.debug("Unregistered %s from generated manifest", key)


async def startup_materialize() -> None:
    """Materialize all active custom networks from DB to disk at startup."""
    ensure_generated_dir()
    factory = get_session_factory()
    if factory is None:
        return
    async with factory() as db:
        nets = await AgentNetworkRepository(db).list_all_active()
        materialize_all(nets)
        logger.info("Materialized %d custom networks at startup", len(nets))


def invalidate_caches() -> None:
    """Reset session_manager caches so next access re-parses manifests.

    This picks up newly materialized/dematerialized networks.
    """
    # Import here to avoid circular imports at module level
    import apps.cruse.backend.session_manager as sm  # pylint: disable=import-outside-toplevel

    sm._systems_cache = None  # pylint: disable=protected-access
    sm._factory_cache = None  # pylint: disable=protected-access
    sm._direct_factory_cache = None  # pylint: disable=protected-access
    logger.info("Invalidated session_manager caches (systems, factory, direct_factory)")

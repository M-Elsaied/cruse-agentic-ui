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
import threading
import time
import uuid

from neuro_san.client.agent_session_factory import AgentSessionFactory
from neuro_san.client.direct_agent_session_factory import DirectAgentSessionFactory
from neuro_san.client.streaming_input_processor import StreamingInputProcessor
from neuro_san.internals.chat.connectivity_reporter import ConnectivityReporter
from neuro_san.internals.graph.persistence.registry_manifest_restorer import RegistryManifestRestorer

from apps.cruse.backend.debug_message_processor import DebugMessageProcessor
from apps.cruse.cruse_assistant import tear_down_cruse_assistant

logger = logging.getLogger(__name__)

# The CRUSE agent network name as registered in the manifest.
# The manifest key "experimental/cruse_agent.hocon" maps to network name "experimental/cruse_agent".
CRUSE_AGENT_NETWORK_NAME = "experimental/cruse_agent"

# ── Caches ────────────────────────────────────────────────────────
# Both RegistryManifestRestorer and DirectAgentSessionFactory parse
# the full manifest (82+ HOCON files). Caching avoids repeated I/O.

_systems_cache: list[str] | None = None  # pylint: disable=invalid-name,useless-suppression
_systems_cache_lock = threading.Lock()

_factory_cache: AgentSessionFactory | None = None  # pylint: disable=invalid-name,useless-suppression
_factory_cache_lock = threading.Lock()

_direct_factory_cache: DirectAgentSessionFactory | None = None  # pylint: disable=invalid-name,useless-suppression
_direct_factory_cache_lock = threading.Lock()


def _get_cached_direct_factory() -> DirectAgentSessionFactory:
    """Return a cached DirectAgentSessionFactory singleton.

    Used for operations that need direct access to AgentNetwork objects
    (e.g. connectivity reporting) without creating a full session.
    """
    global _direct_factory_cache  # pylint: disable=global-statement
    if _direct_factory_cache is None:
        with _direct_factory_cache_lock:
            if _direct_factory_cache is None:
                logger.info("Initializing DirectAgentSessionFactory (one-time)...")
                _direct_factory_cache = DirectAgentSessionFactory()
                logger.info("DirectAgentSessionFactory ready.")
    return _direct_factory_cache


def _get_cached_factory() -> AgentSessionFactory:
    """Return a cached AgentSessionFactory singleton.

    DirectAgentSessionFactory.__init__() runs RegistryManifestRestorer
    which parses every HOCON in the manifest. We only need to do this once.
    """
    global _factory_cache  # pylint: disable=global-statement
    if _factory_cache is None:
        with _factory_cache_lock:
            if _factory_cache is None:
                logger.info("Initializing AgentSessionFactory (one-time)...")
                _factory_cache = AgentSessionFactory()
                logger.info("AgentSessionFactory ready.")
    return _factory_cache


def get_connectivity_for_network(agent_network_name: str) -> dict:
    """Return the connectivity topology of an agent network.

    Uses ConnectivityReporter to introspect the network's agent graph
    without creating a full CruseSession (no LLM init needed).

    :param agent_network_name: Network name as registered in the manifest
                               (e.g. 'basic/hello_world').
    :return: Dict with 'connectivity_info' list and optional 'metadata'.
    """
    os.environ.setdefault("AGENT_MANIFEST_FILE", "registries/manifest.hocon")
    os.environ.setdefault("AGENT_TOOL_PATH", "coded_tools")

    factory = _get_cached_direct_factory()
    agent_network = factory.get_agent_network(agent_network_name)
    reporter = ConnectivityReporter(agent_network)
    connectivity_info = reporter.report_network_connectivity()

    metadata = {}
    try:
        config = agent_network.get_config()
        if "metadata" in config:
            metadata = config["metadata"]
    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug("Could not extract metadata for %s", agent_network_name)

    return {
        "connectivity_info": connectivity_info,
        "metadata": metadata,
    }


def get_cruse_connectivity(target_network_name: str) -> dict:
    """Return merged connectivity of the CRUSE orchestrator + the target network.

    The CRUSE session wraps a target agent network via the ``domain_expert``
    coded tool.  This function returns a unified graph that shows the full
    call chain the user will see in trace events: CRUSE front-man →
    domain_expert → target network's front-man → ...

    :param target_network_name: The user-selected network name.
    :return: Dict with merged 'connectivity_info' and metadata.
    """
    os.environ.setdefault("AGENT_MANIFEST_FILE", "registries/manifest.hocon")
    os.environ.setdefault("AGENT_TOOL_PATH", "coded_tools")

    factory = _get_cached_direct_factory()

    # 1. Get CRUSE orchestrator connectivity
    cruse_network = factory.get_agent_network(CRUSE_AGENT_NETWORK_NAME)
    cruse_reporter = ConnectivityReporter(cruse_network)
    cruse_info = cruse_reporter.report_network_connectivity()

    # 2. Get target network connectivity
    target_network = factory.get_agent_network(target_network_name)
    target_reporter = ConnectivityReporter(target_network)
    target_info = target_reporter.report_network_connectivity()

    # 3. Merge: link domain_expert -> target front-man
    #    The domain_expert coded tool delegates to the target network at
    #    runtime.  We model this by adding the target front-man as a child
    #    of domain_expert so the graph is connected.
    target_root = target_info[0]["origin"] if target_info else None

    merged = []
    for node in cruse_info:
        entry = dict(node)
        if target_root and entry["origin"] == "domain_expert":
            # Add target root as a child of domain_expert
            entry["tools"] = list(entry.get("tools", [])) + [target_root]
        merged.append(entry)

    # Add all target nodes (skip duplicates by origin name)
    seen = {n["origin"] for n in merged}
    for node in target_info:
        if node["origin"] not in seen:
            merged.append(node)
            seen.add(node["origin"])

    # Metadata from the target network
    metadata = {}
    try:
        config = target_network.get_config()
        if "metadata" in config:
            metadata = config["metadata"]
    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug("Could not extract metadata for %s", target_network_name)

    return {
        "connectivity_info": merged,
        "metadata": metadata,
    }


def _create_cruse_session(selected_agent: str):
    """Create a CRUSE agent session with the correct network name.

    This mirrors cruse_assistant.set_up_cruse_assistant() but uses the
    full agent network name (including directory prefix) so the
    DirectAgentSessionFactory can find it in its storage.

    :param selected_agent: The downstream agent network the user selected
                          (e.g. 'agent_network_designer.hocon').
    :return: Tuple of (session, state_info).
    """
    t0 = time.time()
    agent_name = CRUSE_AGENT_NETWORK_NAME
    connection = "direct"
    host = "localhost"
    port = 30011
    local_externals_direct = False
    metadata = {"user_id": os.environ.get("USER")}
    # Ensure .hocon extension is present for the CallAgent file-based lookup
    agent_ref = selected_agent if selected_agent.endswith(".hocon") else selected_agent + ".hocon"
    selected_agent_path = "registries/" + agent_ref

    factory = _get_cached_factory()
    t1 = time.time()
    print(f"[TIMING] _get_cached_factory took {t1 - t0:.2f}s", flush=True)
    session = factory.create_session(connection, agent_name, host, port, local_externals_direct, metadata)
    print(f"[TIMING] factory.create_session took {time.time() - t1:.2f}s", flush=True)
    sly_data = {"selected_agent": selected_agent_path, "agent_session": session}

    cruse_state_info = {
        "last_chat_response": None,
        "prompt": "Please enter your response ('quit' to terminate):\n",
        "timeout": 5000.0,
        "num_input": 0,
        "user_input": None,
        "sly_data": sly_data,
        "chat_filter": {"chat_filter_type": "MAXIMAL"},
    }
    return session, cruse_state_info


def _cruse_chat(session, state_info, user_input: str, debug_processor: DebugMessageProcessor | None = None):
    """Process a single turn of user input.

    Mirrors cruse_assistant.cruse() but can be called with the session
    objects from _create_cruse_session().

    :param session: The active agent session.
    :param state_info: The conversation state dict.
    :param user_input: The user's message text.
    :param debug_processor: Optional debug message processor to attach.
    :return: Tuple of (response_text, updated_state_info).
    """
    t0 = time.time()
    thinking_file = os.environ.get("THINKING_FILE", "/tmp/agent_thinking.txt")
    input_processor = StreamingInputProcessor(
        "DEFAULT",
        thinking_file,
        session,
        None,
    )
    if debug_processor is not None:
        input_processor.get_message_processor().add_processor(debug_processor)
    t1 = time.time()
    print(f"[TIMING] StreamingInputProcessor created in {t1 - t0:.2f}s", flush=True)
    state_info["user_input"] = user_input
    state_info = input_processor.process_once(state_info)
    t2 = time.time()
    print(f"[TIMING] process_once() completed in {t2 - t1:.2f}s", flush=True)
    last_chat_response = state_info.get("last_chat_response")
    return last_chat_response, state_info


class CruseSession:  # pylint: disable=too-many-instance-attributes
    """Holds state for a single CRUSE chat session.

    Uses eager background initialization: the expensive agent session starts
    building as soon as the session is created (POST /api/session). If the
    first chat message arrives before init finishes, it blocks until ready.
    """

    def __init__(self, session_id: str, agent_network: str, user_id: str = "anonymous"):
        self.session_id = session_id
        self.agent_network = agent_network
        self.user_id = user_id
        self.created_at = time.time()
        self.message_count = 0
        self.session = None
        self.state_info = None
        self._initialized = False
        self._init_lock = threading.Lock()
        self._init_error: Exception | None = None
        self.conversation_id: int | None = None
        self.debug_processor = DebugMessageProcessor()

    def start_eager_init(self):
        """Kick off agent session creation in a background thread.

        Called immediately after session creation so the ~13s init
        runs concurrently while the frontend connects the WebSocket.
        """
        thread = threading.Thread(target=self._do_init, daemon=True)
        thread.start()

    def _do_init(self):
        """Perform the actual initialization (runs in background thread)."""
        with self._init_lock:
            if self._initialized:
                return
            try:
                t0 = time.time()
                print(f"[TIMING] Eager init starting for {self.agent_network}...", flush=True)
                self.session, self.state_info = _create_cruse_session(self.agent_network)
                self._initialized = True
                print(f"[TIMING] Eager init complete for {self.agent_network} in {time.time() - t0:.2f}s", flush=True)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self._init_error = exc
                print(f"[TIMING] Eager init FAILED for {self.agent_network}: {exc}", flush=True)
                logger.exception("Eager init failed for %s", self.agent_network)

    def _ensure_initialized(self):
        """Block until eager init is complete. Falls back to synchronous init."""
        if self._initialized:
            return
        with self._init_lock:
            if self._initialized:
                return
            if self._init_error is not None:
                raise self._init_error
            # Fallback: if start_eager_init was never called
            t0 = time.time()
            print(f"[TIMING] Fallback sync init for {self.agent_network}...", flush=True)
            self.session, self.state_info = _create_cruse_session(self.agent_network)
            self._initialized = True
            print(f"[TIMING] Fallback sync init complete in {time.time() - t0:.2f}s", flush=True)

    def chat(self, user_input: str) -> str:
        """Send a message and get the response.

        :param user_input: The user's message.
        :return: The agent's response text.
        """
        t_start = time.time()
        self._ensure_initialized()
        t_init = time.time()
        print(f"[TIMING] _ensure_initialized took {t_init - t_start:.2f}s", flush=True)
        response, self.state_info = _cruse_chat(
            self.session,
            self.state_info,
            user_input,
            self.debug_processor,
        )
        self.message_count += 1
        t_end = time.time()
        print(f"[TIMING] _cruse_chat took {t_end - t_init:.2f}s, total chat() {t_end - t_start:.2f}s", flush=True)
        return response

    def close(self):
        """Tear down the underlying agent session."""
        if self.session is not None:
            try:
                tear_down_cruse_assistant(self.session)
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception("Error tearing down session %s", self.session_id)


class SessionManager:
    """Manages multiple concurrent CRUSE sessions keyed by UUID."""

    def __init__(self):
        self._sessions: dict[str, CruseSession] = {}

    def create_session(self, agent_network: str, user_id: str = "anonymous") -> str:
        """Create a new session and return its ID.

        Immediately kicks off agent session initialization in a background
        thread so the ~13s setup runs while the frontend connects its
        WebSocket and the user starts typing.

        :param agent_network: The HOCON path of the agent network to connect to.
        :param user_id: The authenticated user's ID.
        :return: The UUID session ID.
        """
        session_id = str(uuid.uuid4())
        cruse_session = CruseSession(session_id, agent_network, user_id)
        self._sessions[session_id] = cruse_session
        cruse_session.start_eager_init()
        logger.info("Created session %s for network %s user %s", session_id, agent_network, user_id)
        return session_id

    def get_session(self, session_id: str) -> CruseSession | None:
        """Get a session by ID, or None if not found."""
        return self._sessions.get(session_id)

    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session and clean up resources.

        :param session_id: The session ID to destroy.
        :return: True if the session was found and destroyed, False otherwise.
        """
        session = self._sessions.pop(session_id, None)
        if session is None:
            return False
        session.close()
        logger.info("Destroyed session %s", session_id)
        return True

    def list_sessions(self) -> list[dict]:
        """Return a list of active sessions."""
        return [
            {
                "session_id": sid,
                "agent_network": s.agent_network,
                "user_id": s.user_id,
                "created_at": s.created_at,
            }
            for sid, s in self._sessions.items()
        ]

    def list_sessions_for_user(self, user_id: str) -> list[dict]:
        """Return sessions belonging to a specific user."""
        return [info for info in self.list_sessions() if info["user_id"] == user_id]

    def get_stats(self) -> dict:
        """Return usage statistics for the admin console."""
        sessions = list(self._sessions.values())
        sessions_by_user: dict[str, int] = {}
        sessions_by_network: dict[str, int] = {}
        total_messages = 0
        for s in sessions:
            sessions_by_user[s.user_id] = sessions_by_user.get(s.user_id, 0) + 1
            sessions_by_network[s.agent_network] = sessions_by_network.get(s.agent_network, 0) + 1
            total_messages += s.message_count
        return {
            "total_sessions": len(sessions),
            "active_sessions": len(sessions),
            "total_messages": total_messages,
            "sessions_by_user": sessions_by_user,
            "sessions_by_network": sessions_by_network,
        }

    @staticmethod
    def get_available_systems() -> list[str]:
        """Return the list of available public agent networks from the manifest.

        Uses the Neuro SAN RegistryManifestRestorer which properly resolves
        include directives and path references, unlike raw pyhocon parsing.
        Excludes the cruse_agent itself (it's the orchestrator, not a target).

        Results are cached after the first call since agent networks don't
        change at runtime. This avoids re-parsing 82+ HOCON files on every
        page refresh.
        """
        global _systems_cache  # pylint: disable=global-statement
        if _systems_cache is not None:
            return _systems_cache

        with _systems_cache_lock:
            if _systems_cache is not None:
                return _systems_cache

            os.environ.setdefault("AGENT_MANIFEST_FILE", "registries/manifest.hocon")
            os.environ.setdefault("AGENT_TOOL_PATH", "coded_tools")

            excluded = {"experimental/cruse_agent"}

            logger.info("Parsing manifest for available systems (one-time)...")
            restorer = RegistryManifestRestorer()
            manifest_networks = restorer.restore()

            # "public" storage contains networks marked as public in the manifest
            public_networks = manifest_networks.get("public", {})
            _systems_cache = [name for name in sorted(public_networks.keys()) if name not in excluded]
            logger.info("Found %d available systems.", len(_systems_cache))
            return _systems_cache

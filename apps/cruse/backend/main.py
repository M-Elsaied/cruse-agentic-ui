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

import asyncio
import logging
import os

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from apps.cruse.backend.auth import ClerkUser
from apps.cruse.backend.auth import clerk_verifier
from apps.cruse.backend.auth import get_current_user
from apps.cruse.backend.auth import require_admin
from apps.cruse.backend.auth import verify_ws_token
from apps.cruse.backend.log_capture import LogRingBuffer
from apps.cruse.backend.models import ChatMessage
from apps.cruse.backend.models import ServerEventType
from apps.cruse.backend.models import SessionCreate
from apps.cruse.backend.session_manager import SessionManager
from apps.cruse.backend.session_manager import get_cruse_connectivity
from apps.cruse.backend.session_store import SessionTimeoutManager
from apps.cruse.backend.streaming_bridge import process_chat_message
from apps.cruse.backend.streaming_bridge import send_event
from apps.cruse.backend.theme_service import get_sample_queries_for_network
from apps.cruse.backend.theme_service import get_theme_for_network

logger = logging.getLogger(__name__)

# Ensure environment is set before any agent code runs
os.environ.setdefault("AGENT_MANIFEST_FILE", "registries/manifest.hocon")
os.environ.setdefault("AGENT_TOOL_PATH", "coded_tools")

app = FastAPI(
    title="CRUSE Next-Gen Backend",
    description="FastAPI + WebSocket backend for CRUSE (Context Reactive User Experience)",
    version="2.0.0",
)

# CORS: configurable via ALLOWED_ORIGINS env var (comma-separated).
# When set, parse the comma-separated string into a list of origins.
# When unset, fall back to the default local development origins.
_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]
_origins_env = os.environ.get("ALLOWED_ORIGINS")
_allowed_origins = [o.strip() for o in _origins_env.split(",") if o.strip()] if _origins_env else _DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_manager = SessionManager()
timeout_manager = SessionTimeoutManager(session_manager)
log_buffer = LogRingBuffer(maxlen=500)


# ─── REST Endpoints ──────────────────────────────────────────────


@app.get("/api/health")
async def health_check():
    """Unauthenticated health check for load balancers and Docker."""
    return {"status": "healthy"}


@app.get("/api/systems")
async def list_systems(_user: ClerkUser = Depends(get_current_user)):
    """Return the list of available agent networks."""
    try:
        systems = session_manager.get_available_systems()
        return {"systems": systems}
    except Exception as exc:
        logger.exception("Failed to list systems")
        raise HTTPException(status_code=500, detail="Failed to retrieve available systems") from exc


@app.post("/api/session")
async def create_session(body: SessionCreate, user: ClerkUser = Depends(get_current_user)):
    """Create a new CRUSE chat session for the specified agent network.

    Session creation is instant (lazy init). The expensive agent session
    setup happens on the first chat message instead.
    """
    try:
        session_id = session_manager.create_session(body.agent_network, user.user_id)
        timeout_manager.touch(session_id)
        theme = get_theme_for_network(body.agent_network)
        sample_queries = get_sample_queries_for_network(body.agent_network)
        return {
            "session_id": session_id,
            "agent_network": body.agent_network,
            "theme": theme,
            "sample_queries": sample_queries,
        }
    except Exception as exc:
        logger.exception("Failed to create session for %s", body.agent_network)
        raise HTTPException(status_code=500, detail="Failed to create session") from exc


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str, user: ClerkUser = Depends(get_current_user)):
    """Destroy an existing chat session."""
    cruse_session = session_manager.get_session(session_id)
    if cruse_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if cruse_session.user_id != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this session")
    session_manager.destroy_session(session_id)
    timeout_manager.remove(session_id)
    return {"status": "destroyed", "session_id": session_id}


@app.get("/api/sessions")
async def list_sessions(user: ClerkUser = Depends(get_current_user)):
    """List active sessions. Admins see all; users see only their own."""
    if user.role == "admin":
        return {"sessions": session_manager.list_sessions()}
    return {"sessions": session_manager.list_sessions_for_user(user.user_id)}


@app.get("/api/connectivity/{agent_network:path}")
async def get_network_connectivity(agent_network: str, _user: ClerkUser = Depends(get_current_user)):
    """Return the merged CRUSE + target network connectivity.

    Returns the full call graph that includes the CRUSE orchestrator layer
    (cruse, domain_expert, widget_generator, template_provider) linked into
    the target network's agents.  This matches the agent names that appear
    in real-time trace events.
    """
    try:
        result = await asyncio.to_thread(get_cruse_connectivity, agent_network)
        return result
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=f"Agent network '{agent_network}' not found") from exc
    except Exception as exc:
        logger.exception("Failed to get connectivity for %s", agent_network)
        raise HTTPException(status_code=500, detail="Failed to retrieve network connectivity") from exc


# ─── WebSocket Endpoint ──────────────────────────────────────────


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str, token: str = Query(None)):
    """WebSocket endpoint for real-time chat with a CRUSE session.

    Protocol:
        Client sends: {"text": "...", "form_data": {...}}
        Server emits: {"type": "<event_type>", "data": <payload>}

    Event types:
        - chat_token: Streaming text delta (Phase 4)
        - chat_complete: Complete parsed chat message
        - widget_schema: JSON Schema for dynamic form rendering
        - theme: Background theme definition
        - agent_activity: Agent chain status updates
        - done: Response cycle complete
        - error: Error occurred
    """
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    ws_user = await verify_ws_token(token)
    if ws_user is None:
        await websocket.close(code=4003, reason="Invalid authentication token")
        return

    cruse_session = session_manager.get_session(session_id)
    if cruse_session is None:
        await websocket.close(code=4004, reason="Session not found")
        return

    if cruse_session.user_id != ws_user.user_id and ws_user.role != "admin":
        await websocket.close(code=4003, reason="Not authorized for this session")
        return

    await websocket.accept()
    logger.info("WebSocket connected for session %s", session_id)

    try:
        while True:
            raw = await websocket.receive_json()
            msg = ChatMessage(**raw)

            # Combine text and form data into the user input string
            user_input = msg.text
            if msg.form_data:
                user_input = f"{msg.text}\n\nForm submission context: {msg.form_data}"

            timeout_manager.touch(session_id)
            await process_chat_message(websocket, cruse_session, user_input, log_buffer)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session %s", session_id)
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("WebSocket error for session %s", session_id)
        try:
            await send_event(websocket, ServerEventType.ERROR, {"message": "Connection error"})
        except Exception:  # pylint: disable=broad-exception-caught
            pass


# ─── User Info ───────────────────────────────────────────────────


@app.get("/api/me")
async def get_me(user: ClerkUser = Depends(get_current_user)):
    """Return the authenticated user's info including role."""
    return {"user_id": user.user_id, "email": user.email, "role": user.role}


# ─── Admin Endpoints ─────────────────────────────────────────────


@app.get("/api/admin/sessions")
async def admin_list_sessions(_user: ClerkUser = Depends(require_admin)):
    """List all active sessions (admin only)."""
    return {"sessions": session_manager.list_sessions()}


@app.get("/api/admin/stats")
async def admin_stats(_user: ClerkUser = Depends(require_admin)):
    """Return usage statistics (admin only)."""
    return session_manager.get_stats()


@app.delete("/api/admin/session/{session_id}")
async def admin_delete_session(session_id: str, _user: ClerkUser = Depends(require_admin)):
    """Force-destroy any session (admin only)."""
    destroyed = session_manager.destroy_session(session_id)
    if not destroyed:
        raise HTTPException(status_code=404, detail="Session not found")
    timeout_manager.remove(session_id)
    return {"status": "destroyed", "session_id": session_id}


# ─── Startup / Shutdown ──────────────────────────────────────────


@app.on_event("startup")
async def startup():
    """Start background tasks and warm caches."""
    logger.info("CRUSE Next-Gen backend starting...")
    await clerk_verifier.init()
    # Attach the log ring buffer to the root logger for debug streaming
    log_buffer.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(log_buffer)
    await timeout_manager.start()

    # Warm the expensive caches in a background thread so the first
    # request doesn't pay the full manifest-parsing cost (~1-3 s).
    def _warm():
        logger.info("Warming caches...")
        session_manager.get_available_systems()
        from apps.cruse.backend.session_manager import (  # pylint: disable=import-outside-toplevel
            _get_cached_direct_factory,
        )
        from apps.cruse.backend.session_manager import _get_cached_factory  # pylint: disable=import-outside-toplevel

        _get_cached_factory()
        _get_cached_direct_factory()
        logger.info("Caches warmed.")

    asyncio.get_event_loop().run_in_executor(None, _warm)


@app.on_event("shutdown")
async def shutdown():
    """Clean up all sessions on shutdown."""
    logger.info("CRUSE Next-Gen backend shutting down...")
    await timeout_manager.stop()
    for info in session_manager.list_sessions():
        session_manager.destroy_session(info["session_id"])

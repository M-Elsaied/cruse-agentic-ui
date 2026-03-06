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
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.auth import ClerkUser
from apps.cruse.backend.auth import clerk_verifier
from apps.cruse.backend.auth import get_current_user
from apps.cruse.backend.auth import require_admin
from apps.cruse.backend.auth import verify_ws_token
from apps.cruse.backend.db.engine import dispose_db
from apps.cruse.backend.db.engine import get_db
from apps.cruse.backend.db.engine import get_session_factory
from apps.cruse.backend.db.engine import init_db
from apps.cruse.backend.db.repositories.conversation_repo import ConversationRepository
from apps.cruse.backend.db.repositories.feedback_repo import FeedbackRepository
from apps.cruse.backend.db.repositories.message_repo import MessageRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository
from apps.cruse.backend.log_capture import LogRingBuffer
from apps.cruse.backend.models import ChatMessage
from apps.cruse.backend.models import ConversationDetailResponse
from apps.cruse.backend.models import ConversationListResponse
from apps.cruse.backend.models import ConversationSummary
from apps.cruse.backend.models import MessageResponse
from apps.cruse.backend.models import RatingRequest
from apps.cruse.backend.models import RatingResponse
from apps.cruse.backend.models import ReportListResponse
from apps.cruse.backend.models import ReportRequest
from apps.cruse.backend.models import ReportResponse
from apps.cruse.backend.models import ServerEventType
from apps.cruse.backend.models import SessionCreate
from apps.cruse.backend.rate_limiter import RateLimiter
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
rate_limiter = RateLimiter()


# ─── REST Endpoints ──────────────────────────────────────────────


@app.get("/api/health")
async def health_check():
    """Unauthenticated health check for load balancers and Docker."""
    db_status = "connected"
    try:
        factory = get_session_factory()
        if factory is not None:
            async with factory() as session:
                await session.execute(text("SELECT 1"))
        else:
            db_status = "not_initialized"
    except Exception:  # pylint: disable=broad-exception-caught
        db_status = "disconnected"
    return {"status": "healthy", "database": db_status}


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

        # Best-effort: create conversation record in DB
        factory = get_session_factory()
        if factory is not None:
            try:
                async with factory() as db:
                    conv = await ConversationRepository(db).create(session_id, user.user_id, body.agent_network)
                    await db.commit()
                    cruse_session = session_manager.get_session(session_id)
                    if cruse_session:
                        cruse_session.conversation_id = conv.id
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception("Failed to create conversation record for session %s", session_id)

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
async def websocket_chat(websocket: WebSocket, session_id: str, token: str = Query(None)):  # pylint: disable=too-many-branches,too-many-locals,too-many-statements
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

            # Rate-limit check (admins bypass) — uses DB session
            factory = get_session_factory()
            if factory is not None:
                async with factory() as db:
                    # Upsert user on every message (keeps DB in sync with Clerk)
                    await UserRepository(db).upsert_from_clerk(
                        ws_user.user_id, ws_user.email, ws_user.name, ws_user.role
                    )
                    allowed, remaining, limit = await rate_limiter.check_and_increment(
                        ws_user.user_id, ws_user.role, db
                    )
                    await db.commit()
            else:
                # Fallback: no DB available, allow request
                allowed, remaining, limit = True, None, None

            if not allowed:
                await send_event(
                    websocket,
                    ServerEventType.RATE_LIMIT,
                    {"allowed": False, "remaining": 0, "limit": limit},
                )
                await send_event(websocket, ServerEventType.DONE, None)
                continue

            # Notify non-admin users of remaining quota before processing
            if remaining is not None:
                await send_event(
                    websocket,
                    ServerEventType.RATE_LIMIT,
                    {"allowed": True, "remaining": remaining, "limit": limit},
                )

            # Best-effort: save user message to DB
            if cruse_session.conversation_id is not None and factory is not None:
                try:
                    async with factory() as msg_db:
                        user_metadata = {}
                        if msg.form_data:
                            user_metadata["form_data"] = msg.form_data
                        await MessageRepository(msg_db).append(
                            cruse_session.conversation_id, "user", user_input, metadata=user_metadata or None
                        )
                        if cruse_session.message_count == 0:
                            # Use original text (not augmented user_input) for clean titles
                            title_src = str(msg.text).strip()
                            title = title_src[:80].rsplit(" ", 1)[0] if len(title_src) > 80 else title_src
                            await ConversationRepository(msg_db).update_title(cruse_session.conversation_id, title)
                        await msg_db.commit()
                except Exception:  # pylint: disable=broad-exception-caught
                    logger.exception("Failed to save user message")

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
    """Return the authenticated user's info including role and rate limit."""
    result: dict = {"user_id": user.user_id, "email": user.email, "role": user.role}

    # DB operations are best-effort — if the database is unavailable
    # we still return user info from the JWT.
    factory = get_session_factory()
    if factory is not None:
        try:
            async with factory() as db:
                await UserRepository(db).upsert_from_clerk(user.user_id, user.email, user.name, user.role)
                remaining, limit = await rate_limiter.get_remaining(user.user_id, user.role, db)
                if remaining is not None:
                    result["rate_limit"] = {"remaining": remaining, "limit": limit}
                await db.commit()
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception("Database error in /api/me — returning JWT-only response")

    return result


# ─── Conversation History ────────────────────────────────────────


@app.get("/api/conversations")
async def list_conversations(
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_archived: bool = Query(False),
):
    """List the authenticated user's conversations, most recent first."""
    rows = await ConversationRepository(db).list_with_counts(
        user.user_id, include_archived=include_archived, limit=limit + 1, offset=offset
    )
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]
    conversations = [
        ConversationSummary(
            id=conv.id,
            session_id=conv.session_id,
            agent_network=conv.agent_network,
            title=conv.title,
            is_archived=conv.is_archived,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
            message_count=msg_count,
        )
        for conv, msg_count in rows
    ]
    return ConversationListResponse(conversations=conversations, total=len(conversations), has_more=has_more)


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all its messages."""
    conv = await ConversationRepository(db).get_with_messages(conversation_id)
    if conv is None or (conv.user_id != user.user_id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Filter out internal metadata (agent traces, latency) — only expose user-facing data
    _internal_keys = {"agent_trace", "latency_ms"}
    messages = [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            metadata={k: v for k, v in (m.metadata_ or {}).items() if k not in _internal_keys},
            created_at=m.created_at.isoformat(),
        )
        for m in conv.messages
    ]
    summary = ConversationSummary(
        id=conv.id,
        session_id=conv.session_id,
        agent_network=conv.agent_network,
        title=conv.title,
        is_archived=conv.is_archived,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
        message_count=len(messages),
    )
    return ConversationDetailResponse(conversation=summary, messages=messages)


@app.delete("/api/conversations/{conversation_id}")
async def archive_conversation(
    conversation_id: int,
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive (soft-delete) a conversation."""
    conv = await ConversationRepository(db).get_by_id(conversation_id)
    if conv is None or (conv.user_id != user.user_id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Conversation not found")
    await ConversationRepository(db).archive(conversation_id)
    return {"status": "archived", "conversation_id": conversation_id}


# ─── Feedback ────────────────────────────────────────────────────


async def _verify_message_ownership(message_id: int, user: ClerkUser, db: AsyncSession):
    """Load a message and verify the requesting user owns the parent conversation (or is admin).

    Returns 404 for both missing and unauthorized messages to prevent IDOR enumeration.
    """
    msg = await MessageRepository(db).get_by_id(message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    conv = await ConversationRepository(db).get_by_id(msg.conversation_id)
    if conv is None or (conv.user_id != user.user_id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Message not found")
    return msg, conv


@app.post("/api/messages/{message_id}/rating", response_model=RatingResponse)
async def post_rating(
    message_id: int,
    body: RatingRequest,
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add or update a thumbs up/down rating on a message."""
    if body.rating not in (-1, 1):
        raise HTTPException(status_code=422, detail="Rating must be -1 or 1")
    await _verify_message_ownership(message_id, user, db)
    fb = await FeedbackRepository(db).add_rating(message_id, user.user_id, body.rating, comment=body.comment)
    return RatingResponse(id=fb.id, message_id=message_id, rating=fb.rating, comment=fb.comment)


@app.delete("/api/messages/{message_id}/rating", status_code=204)
async def delete_rating(
    message_id: int,
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a user's rating from a message."""
    await _verify_message_ownership(message_id, user, db)
    deleted = await FeedbackRepository(db).delete_rating(message_id, user.user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rating not found")


@app.post("/api/reports", response_model=ReportResponse)
async def post_report(
    body: ReportRequest,
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a feedback report (bug, feature request, or general)."""
    context: dict = {}
    conversation_id = body.conversation_id
    message_id = body.message_id

    # Auto-attach agent trace from the referenced message (with ownership check)
    if message_id is not None:
        msg = await MessageRepository(db).get_by_id(message_id)
        if msg is not None:
            # Verify the user owns the message's conversation (or is admin)
            conv = await ConversationRepository(db).get_by_id(msg.conversation_id)
            if conv is None or (conv.user_id != user.user_id and user.role != "admin"):
                raise HTTPException(status_code=403, detail="Not authorized to reference this message")
            if msg.metadata_:
                agent_trace = msg.metadata_.get("agent_trace")
                if agent_trace:
                    context["agent_trace"] = agent_trace
            # Derive conversation_id from message if not explicitly provided
            if conversation_id is None:
                conversation_id = msg.conversation_id

    # Enrich context from the conversation record (with ownership check)
    if conversation_id is not None:
        conv = await ConversationRepository(db).get_by_id(conversation_id)
        if conv is not None:
            if conv.user_id != user.user_id and user.role != "admin":
                raise HTTPException(status_code=403, detail="Not authorized to reference this conversation")
            context["agent_network"] = conv.agent_network
            context["session_id"] = conv.session_id

    report = await FeedbackRepository(db).add_report(
        user.user_id,
        body.body,
        category=body.category,
        conversation_id=conversation_id,
        message_id=message_id,
        context=context or None,
    )
    return ReportResponse(
        id=report.id,
        category=report.category,
        body=report.body,
        status=report.status,
        created_at=report.created_at.isoformat(),
    )


@app.get("/api/admin/reports", response_model=ReportListResponse)
async def admin_list_reports(
    _user: ClerkUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List feedback reports (admin only)."""
    repo = FeedbackRepository(db)
    reports = await repo.list_reports(status=status, limit=limit, offset=offset)
    total = await repo.count_reports(status=status)
    return ReportListResponse(
        reports=[
            ReportResponse(
                id=r.id,
                category=r.category,
                body=r.body,
                status=r.status,
                created_at=r.created_at.isoformat(),
            )
            for r in reports
        ],
        total=total,
    )


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
    # Load .env.local for local dev (no-op if file absent or vars already set)
    from pathlib import Path  # pylint: disable=import-outside-toplevel

    from dotenv import load_dotenv  # pylint: disable=import-outside-toplevel

    _env_local = Path(__file__).resolve().parent / ".env.local"
    if _env_local.exists():
        load_dotenv(_env_local, override=False)

    logger.info("CRUSE Next-Gen backend starting...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to initialize database — running without persistence")

    await clerk_verifier.init()
    await rate_limiter.init()
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
    """Clean up all sessions and dispose of database connections on shutdown."""
    logger.info("CRUSE Next-Gen backend shutting down...")
    await timeout_manager.stop()
    for info in session_manager.list_sessions():
        session_manager.destroy_session(info["session_id"])
    await dispose_db()

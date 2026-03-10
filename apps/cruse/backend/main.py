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
from apps.cruse.backend.authz.middleware import AuthorizationService
from apps.cruse.backend.authz.openfga_client import openfga_client
from apps.cruse.backend.authz.tuple_manager import TupleManager
from apps.cruse.backend.db.engine import dispose_db
from apps.cruse.backend.db.engine import get_db
from apps.cruse.backend.db.engine import get_session_factory
from apps.cruse.backend.db.engine import init_db
from apps.cruse.backend.db.repositories.api_key_repo import ApiKeyRepository
from apps.cruse.backend.db.repositories.conversation_repo import ConversationRepository
from apps.cruse.backend.db.repositories.feedback_repo import FeedbackRepository
from apps.cruse.backend.db.repositories.message_repo import MessageRepository
from apps.cruse.backend.db.repositories.preference_repo import PreferenceRepository
from apps.cruse.backend.db.repositories.request_log_repo import RequestLogRepository
from apps.cruse.backend.db.repositories.user_repo import UserRepository
from apps.cruse.backend.key_resolver import SUPPORTED_PROVIDERS
from apps.cruse.backend.key_resolver import has_any_valid_key
from apps.cruse.backend.log_capture import LogRingBuffer
from apps.cruse.backend.models import AdminConversationListResponse
from apps.cruse.backend.models import AdminConversationSummary
from apps.cruse.backend.models import AnalyticsOverview
from apps.cruse.backend.models import AnalyticsResponse
from apps.cruse.backend.models import ChatMessage
from apps.cruse.backend.models import ConversationDetailResponse
from apps.cruse.backend.models import ConversationListResponse
from apps.cruse.backend.models import ConversationSummary
from apps.cruse.backend.models import KeyInfo
from apps.cruse.backend.models import KeyListResponse
from apps.cruse.backend.models import KeyStoreRequest
from apps.cruse.backend.models import KeyStoreResponse
from apps.cruse.backend.models import KeyValidateRequest
from apps.cruse.backend.models import KeyValidateResponse
from apps.cruse.backend.models import MessageResponse
from apps.cruse.backend.models import NetworkScorecard
from apps.cruse.backend.models import PreferenceResponse
from apps.cruse.backend.models import PreferenceUpdateRequest
from apps.cruse.backend.models import RatingRequest
from apps.cruse.backend.models import RatingResponse
from apps.cruse.backend.models import ReportListResponse
from apps.cruse.backend.models import ReportRequest
from apps.cruse.backend.models import ReportResponse
from apps.cruse.backend.models import ServerEventType
from apps.cruse.backend.models import SessionCreate
from apps.cruse.backend.models import UserBreakdown
from apps.cruse.backend.models import UserBreakdownResponse
from apps.cruse.backend.network_routes import get_custom_networks_summary
from apps.cruse.backend.network_routes import router as network_router
from apps.cruse.backend.rate_limiter import RateLimiter
from apps.cruse.backend.session_manager import SessionManager
from apps.cruse.backend.session_manager import get_cruse_connectivity
from apps.cruse.backend.session_store import SessionTimeoutManager
from apps.cruse.backend.streaming_bridge import process_chat_message
from apps.cruse.backend.streaming_bridge import send_event
from apps.cruse.backend.tenant_context import resolve_tenant_context
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
tuple_manager = TupleManager(openfga_client)
authz_service = AuthorizationService(openfga_client)

app.include_router(network_router)


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
    fga_status = "connected" if openfga_client.is_initialized else "not_initialized"
    return {"status": "healthy", "database": db_status, "openfga": fga_status}


@app.get("/api/systems")
async def list_systems(
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the list of available agent networks, categorized.

    Includes built-in networks (from manifest) plus custom networks
    (from DB: user-owned and shared within org).
    """
    try:
        systems = session_manager.get_available_systems()
        if user.role != "admin":
            systems = [s for s in systems if s.startswith(("industry/", "experimental/"))]

        # Categorize built-in networks
        categorized: dict[str, list[str]] = {}
        for s in systems:
            category = s.split("/")[0] if "/" in s else "other"
            categorized.setdefault(category, []).append(s)

        result: dict = {"systems": systems, "categories": categorized}

        result["custom_networks"] = await get_custom_networks_summary(user, db)

        return result
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
                    # Resolve org for this session
                    tenant = await resolve_tenant_context(user, db)
                    conv = await ConversationRepository(db).create(
                        session_id, user.user_id, body.agent_network, org_id=tenant.org_id
                    )
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


# ─── Settings / BYOK Endpoints ───────────────────────────────────


@app.get("/api/settings/keys", response_model=KeyListResponse)
async def list_keys(
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the user's stored API keys (masked, never raw)."""
    providers = await ApiKeyRepository(db).list_providers(user.user_id)
    keys = [
        KeyInfo(
            provider=p["provider"],
            label=p["label"],
            key_hint=p["key_hint"],
            is_valid=p["is_valid"],
            created_at=p["created_at"].isoformat() if p["created_at"] else None,
        )
        for p in providers
    ]
    return KeyListResponse(keys=keys, supported_providers=SUPPORTED_PROVIDERS)


@app.post("/api/settings/keys", response_model=KeyStoreResponse)
async def store_key(
    body: KeyStoreRequest,
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validate and store an API key."""
    from apps.cruse.backend.key_validator import validate_key  # pylint: disable=import-outside-toplevel

    valid, message = await validate_key(body.provider, body.key)
    if not valid:
        raise HTTPException(status_code=422, detail=message)

    api_key = await ApiKeyRepository(db).store(user.user_id, body.provider, body.key, label=body.label)
    return KeyStoreResponse(provider=api_key.provider, key_hint=api_key.key_hint, message="Key stored successfully")


@app.delete("/api/settings/keys/{provider}")
async def delete_key(
    provider: str,
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a stored API key."""
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=422, detail=f"Unsupported provider: {provider}")
    deleted = await ApiKeyRepository(db).delete(user.user_id, provider)
    if not deleted:
        raise HTTPException(status_code=404, detail="No key found for this provider")
    return {"status": "deleted", "provider": provider}


@app.post("/api/settings/keys/validate", response_model=KeyValidateResponse)
async def validate_key_endpoint(
    body: KeyValidateRequest,
    _user: ClerkUser = Depends(get_current_user),
):
    """Validate an API key without storing it."""
    from apps.cruse.backend.key_validator import validate_key  # pylint: disable=import-outside-toplevel

    valid, message = await validate_key(body.provider, body.key)
    return KeyValidateResponse(valid=valid, message=message)


@app.get("/api/settings/preferences", response_model=PreferenceResponse)
async def get_preferences(
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's LLM preferences."""
    pref = await PreferenceRepository(db).get(user.user_id)
    if pref is None:
        return PreferenceResponse()
    return PreferenceResponse(
        preferred_provider=pref.preferred_provider,
        preferred_model=pref.preferred_model,
        settings=pref.settings or {},
    )


@app.put("/api/settings/preferences", response_model=PreferenceResponse)
async def update_preferences(
    body: PreferenceUpdateRequest,
    user: ClerkUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the user's LLM preferences."""
    pref = await PreferenceRepository(db).update(
        user.user_id,
        preferred_provider=body.preferred_provider,
        preferred_model=body.preferred_model,
        settings=body.settings,
    )
    return PreferenceResponse(
        preferred_provider=pref.preferred_provider,
        preferred_model=pref.preferred_model,
        settings=pref.settings or {},
    )


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
                # Seed sly_data with form submission so coded tools (e.g., WidgetTemplateProvider)
                # can surface previously collected fields to the LLM and avoid duplicate widgets.
                ws_sly_data = (
                    cruse_session.state_info.get("sly_data") if cruse_session.state_info is not None else None
                )
                if ws_sly_data is not None:
                    widget_state = ws_sly_data.setdefault("widget_state", {})
                    submitted_fields = widget_state.setdefault("submitted_fields", [])
                    submitted_fields.extend(k for k in msg.form_data if k not in submitted_fields)
                    widget_state.setdefault("submission_data", {}).update(msg.form_data)

            timeout_manager.touch(session_id)

            # Rate-limit check (admins and BYOK users bypass) — uses DB session
            factory = get_session_factory()
            if factory is not None:
                async with factory() as db:
                    # Upsert user on every message (keeps DB in sync with Clerk)
                    await UserRepository(db).upsert_from_clerk(
                        ws_user.user_id, ws_user.email, ws_user.name, ws_user.role
                    )
                    user_has_byok = await has_any_valid_key(ws_user.user_id, db)
                    allowed, remaining, limit = await rate_limiter.check_and_increment(
                        ws_user.user_id, ws_user.role, db, has_byok=user_has_byok
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
    """Return the authenticated user's info including role, org, and rate limit."""
    result: dict = {"user_id": user.user_id, "email": user.email, "role": user.role}

    if user.org_id:
        result["org"] = {"org_id": user.org_id, "org_role": user.org_role, "org_slug": user.org_slug}

    # DB operations are best-effort — if the database is unavailable
    # we still return user info from the JWT.
    factory = get_session_factory()
    if factory is not None:
        try:
            async with factory() as db:
                await UserRepository(db).upsert_from_clerk(user.user_id, user.email, user.name, user.role)
                tenant = await resolve_tenant_context(user, db)
                result["org"] = {
                    "org_id": tenant.org.clerk_org_id,
                    "org_name": tenant.org.name,
                    "org_slug": tenant.org.slug,
                    "is_org_admin": tenant.is_org_admin,
                }
                has_byok = await has_any_valid_key(user.user_id, db)
                result["has_byok"] = has_byok
                result["key_source"] = "personal" if has_byok else "platform"
                remaining, limit = await rate_limiter.get_remaining(user.user_id, user.role, db, has_byok=has_byok)
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
    # Admins see full metadata (agent traces, latency) for debugging
    _internal_keys = {"agent_trace", "latency_ms"} if user.role != "admin" else set()
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

    # Resolve org for this report
    tenant = await resolve_tenant_context(user, db)

    report = await FeedbackRepository(db).add_report(
        user.user_id,
        body.body,
        category=body.category,
        conversation_id=conversation_id,
        message_id=message_id,
        context=context or None,
        org_id=tenant.org_id,
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
                user_id=r.user_id,
                conversation_id=r.conversation_id,
                message_id=r.message_id,
                context=r.context,
            )
            for r in reports
        ],
        total=total,
    )


async def _get_github_installation_token() -> tuple[str, str]:
    """Generate a GitHub App installation token.

    Returns (token, repo_slug).
    Uses GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY_PATH, and GITHUB_REPO env vars.
    """
    import time  # pylint: disable=import-outside-toplevel

    import httpx  # pylint: disable=import-outside-toplevel
    import jwt  # pylint: disable=import-outside-toplevel

    app_id = os.environ.get("GITHUB_APP_ID")
    key_path = os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH")
    repo_slug = os.environ.get("GITHUB_REPO")
    if not app_id or not key_path or not repo_slug:
        raise HTTPException(
            status_code=501,
            detail="GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY_PATH, and GITHUB_REPO env vars required",
        )

    with open(key_path, "r", encoding="utf-8") as fh:
        private_key = fh.read()

    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + (10 * 60), "iss": int(app_id)}
    app_jwt = jwt.encode(payload, private_key, algorithm="RS256")

    headers = {"Authorization": f"Bearer {app_jwt}", "Accept": "application/vnd.github.v3+json"}
    async with httpx.AsyncClient() as client:
        # Find the installation for this repo
        resp = await client.get(f"https://api.github.com/repos/{repo_slug}/installation", headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"GitHub App not installed on {repo_slug}")
        installation_id = resp.json()["id"]

        # Get an installation access token
        resp = await client.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers=headers,
        )
        if resp.status_code != 201:
            raise HTTPException(status_code=502, detail="Failed to get GitHub installation token")
        return resp.json()["token"], repo_slug


@app.post("/api/admin/reports/{report_id}/github-issue")
async def create_github_issue(
    report_id: int,
    _user: ClerkUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a GitHub issue from a feedback report (admin only)."""
    import httpx  # pylint: disable=import-outside-toplevel

    token, repo_slug = await _get_github_installation_token()

    report = await FeedbackRepository(db).get_report_by_id(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    # Build issue body with context metadata
    lines = [f"**Category:** {report.category}", f"**Status:** {report.status}", ""]
    if report.context:
        if report.context.get("agent_network"):
            lines.append(f"**Agent Network:** `{report.context['agent_network']}`")
        if report.context.get("session_id"):
            lines.append(f"**Session ID:** `{report.context['session_id']}`")
        if report.context.get("agent_trace"):
            lines.append(f"**Agent Trace:** {report.context['agent_trace']}")
        lines.append("")
    lines.append("## Description")
    lines.append(report.body)
    lines.append("")
    lines.append(f"---\n*Auto-created from feedback report #{report.id}*")

    label_map = {"bug": "bug", "feature": "enhancement", "general": "feedback"}
    labels = [label_map.get(report.category, "feedback")]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.github.com/repos/{repo_slug}/issues",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={
                "title": f"[{report.category.upper()}] {report.body[:80]}",
                "body": "\n".join(lines),
                "labels": labels,
            },
        )
        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"GitHub API error: {resp.text}")
        issue_data = resp.json()
        return {"issue_url": issue_data["html_url"], "issue_number": issue_data["number"]}


# ─── Admin Endpoints ─────────────────────────────────────────────


@app.get("/api/admin/sessions")
async def admin_list_sessions(
    _user: ClerkUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all active sessions with resolved user identity (admin only)."""
    sessions = session_manager.list_sessions()
    # Resolve user IDs to email/name from the users table
    user_ids = {s["user_id"] for s in sessions}
    if user_ids:
        user_repo = UserRepository(db)
        user_map: dict[str, dict] = {}
        for uid in user_ids:
            u = await user_repo.get_by_id(uid)
            if u:
                user_map[uid] = {"email": u.email, "name": u.name}
        for s in sessions:
            info = user_map.get(s["user_id"], {})
            s["email"] = info.get("email")
            s["name"] = info.get("name")
    return {"sessions": sessions}


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


@app.get("/api/admin/conversations", response_model=AdminConversationListResponse)
async def admin_list_conversations(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    _user: ClerkUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str | None = Query(None),
    agent_network: str | None = Query(None),
    include_archived: bool = Query(False),
):
    """List all conversations across all users (admin only)."""
    rows, total = await ConversationRepository(db).list_all(
        limit=limit + 1,
        offset=offset,
        user_id=user_id,
        agent_network=agent_network,
        include_archived=include_archived,
    )
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]
    conversations = [
        AdminConversationSummary(
            id=conv.id,
            session_id=conv.session_id,
            agent_network=conv.agent_network,
            title=conv.title,
            is_archived=conv.is_archived,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
            message_count=msg_count,
            user_id=conv.user_id,
            user_email=email,
            user_name=name,
        )
        for conv, msg_count, email, name in rows
    ]
    return AdminConversationListResponse(conversations=conversations, total=total, has_more=has_more)


# ─── Analytics ────────────────────────────────────────────────────


@app.get("/api/admin/analytics", response_model=AnalyticsResponse)
async def admin_analytics(  # pylint: disable=too-many-locals
    _user: ClerkUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    period_days: int = Query(30, ge=1, le=365),
):
    """Main analytics dashboard payload (admin only).

    Combines request stats, satisfaction scores, and conversation depth
    into a single response to avoid multiple round-trips.
    """
    req_repo = RequestLogRepository(db)
    fb_repo = FeedbackRepository(db)
    conv_repo = ConversationRepository(db)

    overview_raw = await req_repo.get_overview(period_days=period_days)
    satisfaction = await fb_repo.get_satisfaction_score(period_days=period_days)
    open_reports = await fb_repo.count_reports(status="open")
    requests_over_time = await req_repo.get_requests_over_time(period_days=period_days)
    active_users_over_time = await req_repo.get_active_users_over_time(period_days=period_days)
    top_networks = await req_repo.get_top_networks(period_days=period_days)
    network_satisfaction = await fb_repo.get_network_satisfaction(period_days=period_days)
    network_depth = await conv_repo.get_avg_depth_by_network(period_days=period_days)

    # Merge network data: requests + satisfaction + depth into scorecard
    sat_by_network = {s["network"]: s["score"] for s in network_satisfaction}
    depth_by_network = {d["network"]: d["avg_messages"] for d in network_depth}

    scorecard = [
        NetworkScorecard(
            network=n["network"],
            request_count=n["request_count"],
            avg_latency_ms=n["avg_latency_ms"],
            error_rate=n["error_rate"],
            satisfaction_score=sat_by_network.get(n["network"], -1.0),
            avg_depth=depth_by_network.get(n["network"], 0.0),
        )
        for n in top_networks
    ]

    overview = AnalyticsOverview(
        total_requests=overview_raw["total_requests"],
        unique_users=overview_raw["unique_users"],
        avg_latency_ms=overview_raw["avg_latency_ms"],
        error_count=overview_raw["error_count"],
        error_rate=overview_raw["error_rate"],
        satisfaction_score=satisfaction["score"],
        open_reports=open_reports,
        period_days=period_days,
        prev_total_requests=overview_raw["prev_total_requests"],
        prev_unique_users=overview_raw["prev_unique_users"],
        prev_error_rate=overview_raw["prev_error_rate"],
    )

    return AnalyticsResponse(
        overview=overview,
        requests_over_time=requests_over_time,
        active_users_over_time=active_users_over_time,
        network_scorecard=scorecard,
    )


@app.get("/api/admin/analytics/users", response_model=UserBreakdownResponse)
async def admin_analytics_users(
    _user: ClerkUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    period_days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Per-user analytics breakdown (admin only, on-demand)."""
    users, total = await RequestLogRepository(db).get_user_breakdown(
        period_days=period_days, limit=limit, offset=offset
    )
    return UserBreakdownResponse(
        users=[UserBreakdown(**u) for u in users],
        total=total,
    )


@app.get("/api/admin/analytics/export")
async def admin_analytics_export(
    _user: ClerkUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    period_days: int = Query(90, ge=1, le=365),
):
    """Export request log as CSV (admin only). Hard limit 10K rows."""
    import csv  # pylint: disable=import-outside-toplevel
    import io  # pylint: disable=import-outside-toplevel

    from fastapi.responses import StreamingResponse  # pylint: disable=import-outside-toplevel

    rows = await RequestLogRepository(db).get_export_rows(period_days=period_days)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["date", "user_id", "agent_network", "latency_ms", "is_error"])
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=request_log_export.csv"},
    )


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
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to initialize database — running without persistence")

    try:
        from apps.cruse.backend import network_materializer  # pylint: disable=import-outside-toplevel

        await network_materializer.startup_materialize()
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to materialize custom networks at startup")

    await clerk_verifier.init()
    await rate_limiter.init()

    # Initialize OpenFGA authorization
    try:
        await openfga_client.init()
        # Bootstrap built-in network tuples so all users can read them
        systems = session_manager.get_available_systems()
        await tuple_manager.bootstrap_builtin_networks(systems)
        logger.info("OpenFGA initialized with %d built-in network tuples", len(systems))
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to initialize OpenFGA — running without authorization")
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
    await openfga_client.close()
    await dispose_db()

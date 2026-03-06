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

from enum import Enum
from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class SessionCreate(BaseModel):
    """Request body for creating a new chat session."""

    agent_network: str = Field(..., description="The agent network HOCON path to connect to")


class ChatMessage(BaseModel):
    """A chat message sent from the client."""

    text: str = Field(..., max_length=10000, description="The user's message text")
    form_data: Optional[dict[str, Any]] = Field(None, description="Optional form data from widget submission")


class ServerEventType(str, Enum):
    """Types of events the server can emit over WebSocket."""

    CHAT_TOKEN = "chat_token"
    CHAT_COMPLETE = "chat_complete"
    WIDGET_SCHEMA = "widget_schema"
    THEME = "theme"
    AGENT_ACTIVITY = "agent_activity"
    AGENT_TRACE = "agent_trace"
    SERVER_LOG = "server_log"
    RATE_LIMIT = "rate_limit"
    DONE = "done"
    ERROR = "error"


class ServerEvent(BaseModel):
    """A typed event emitted from the server over WebSocket."""

    type: ServerEventType
    data: Any = None


class UserInfo(BaseModel):
    """Represents an authenticated user for API responses."""

    user_id: str
    email: str | None = None
    role: str = "user"


class AdminStats(BaseModel):
    """Usage statistics for the admin console."""

    total_sessions: int
    active_sessions: int
    total_messages: int
    sessions_by_user: dict[str, int]
    sessions_by_network: dict[str, int]


class MessageResponse(BaseModel):
    """A persisted message in a conversation."""

    id: int
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class ConversationSummary(BaseModel):
    """Summary of a conversation for list views."""

    id: int
    session_id: str
    agent_network: str
    title: str | None = None
    is_archived: bool = False
    created_at: str
    updated_at: str
    message_count: int = 0


class ConversationListResponse(BaseModel):
    """Paginated list of conversations."""

    conversations: list[ConversationSummary]
    total: int
    has_more: bool


class ConversationDetailResponse(BaseModel):
    """Full conversation with messages."""

    conversation: ConversationSummary
    messages: list[MessageResponse]


class RatingRequest(BaseModel):
    """Request body for thumbs up/down rating."""

    rating: int = Field(..., description="1 for thumbs up, -1 for thumbs down")
    comment: str | None = Field(None, max_length=2000)


class RatingResponse(BaseModel):
    """Response for a rating operation."""

    id: int
    message_id: int
    rating: int
    comment: str | None = None


class ReportRequest(BaseModel):
    """Request body for submitting a feedback report."""

    body: str = Field(..., min_length=1, max_length=5000)
    category: str = Field("bug", pattern="^(bug|feature|general)$")
    conversation_id: int | None = None
    message_id: int | None = None


class ReportResponse(BaseModel):
    """Response for a created report."""

    id: int
    category: str
    body: str
    status: str
    created_at: str


class ReportListResponse(BaseModel):
    """Paginated list of feedback reports."""

    reports: list[ReportResponse]
    total: int

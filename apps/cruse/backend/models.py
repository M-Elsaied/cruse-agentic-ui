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

    text: str = Field(..., description="The user's message text")
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

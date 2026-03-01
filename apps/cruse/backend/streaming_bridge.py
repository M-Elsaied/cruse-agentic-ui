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
import time

from starlette.websockets import WebSocket

from apps.cruse.backend.log_capture import LogRingBuffer
from apps.cruse.backend.models import ServerEventType
from apps.cruse.backend.response_parser import parse_response_blocks
from apps.cruse.backend.session_manager import CruseSession

logger = logging.getLogger(__name__)


async def send_event(websocket: WebSocket, event_type: ServerEventType, data=None):
    """Send a typed JSON event over the WebSocket.

    :param websocket: The WebSocket connection.
    :param event_type: The event type enum value.
    :param data: Optional data payload.
    """
    await websocket.send_json({"type": event_type.value, "data": data})


async def _drain_debug_events(websocket: WebSocket, cruse_session: CruseSession, log_buffer: LogRingBuffer | None):
    """Drain debug processor and log buffer queues and emit events over WebSocket.

    :param websocket: The WebSocket connection.
    :param cruse_session: The active CRUSE session (has debug_processor).
    :param log_buffer: Optional log ring buffer to drain.
    """
    for entry in cruse_session.debug_processor.drain():
        await send_event(websocket, ServerEventType.AGENT_TRACE, entry)
    if log_buffer is not None:
        for entry in log_buffer.drain():
            await send_event(websocket, ServerEventType.SERVER_LOG, entry)


async def process_chat_message(
    websocket: WebSocket,
    cruse_session: CruseSession,
    user_input: str,
    log_buffer: LogRingBuffer | None = None,
):
    """Process a user message through the CRUSE agent and stream results to the WebSocket.

    Uses CruseSession.chat() which internally calls StreamingInputProcessor.process_once().
    Runs in a thread to avoid blocking the event loop. After the full response is available,
    it parses the response into say/gui blocks and emits structured events.

    :param websocket: The WebSocket connection to send events on.
    :param cruse_session: The active CRUSE session.
    :param user_input: The user's message text.
    :param log_buffer: Optional log ring buffer for server log streaming.
    """
    await send_event(websocket, ServerEventType.AGENT_ACTIVITY, {"status": "thinking", "agents": ["cruse"]})

    try:
        # Run the synchronous chat call in a thread pool.
        # Send periodic keepalive pings and drain debug queues every 2 seconds
        # to provide real-time visibility during long agent processing chains.
        t_bridge_start = time.time()
        print("[TIMING] process_chat_message: dispatching to thread pool", flush=True)
        chat_task = asyncio.ensure_future(asyncio.to_thread(cruse_session.chat, user_input))

        poll_count = 0
        while not chat_task.done():
            await asyncio.sleep(2)
            poll_count += 1
            elapsed = time.time() - t_bridge_start
            print(f"[TIMING] poll #{poll_count}, elapsed={elapsed:.1f}s, task.done={chat_task.done()}", flush=True)
            if not chat_task.done():
                await _drain_debug_events(websocket, cruse_session, log_buffer)
                await send_event(
                    websocket,
                    ServerEventType.AGENT_ACTIVITY,
                    {"status": "thinking", "agents": ["cruse"]},
                )

        response = chat_task.result()
        print(f"[TIMING] process_chat_message: chat completed in {time.time() - t_bridge_start:.2f}s", flush=True)

        # Final drain to catch any remaining debug messages
        await _drain_debug_events(websocket, cruse_session, log_buffer)

        if not response:
            await send_event(websocket, ServerEventType.ERROR, {"message": "No response from agent"})
            await send_event(websocket, ServerEventType.DONE)
            return

        # Parse the response into structured blocks
        blocks = parse_response_blocks(response)

        for kind, content in blocks:
            if kind == "say":
                await send_event(websocket, ServerEventType.CHAT_COMPLETE, content)
            elif kind == "gui_json":
                await send_event(websocket, ServerEventType.WIDGET_SCHEMA, content)
            elif kind == "gui_html":
                # Legacy HTML fallback - send as widget with raw HTML marker
                await send_event(websocket, ServerEventType.WIDGET_SCHEMA, {"_html": content})

    except Exception:
        logger.exception("Error processing chat message")
        await send_event(websocket, ServerEventType.ERROR, {"message": "An error occurred processing your message"})

    await send_event(websocket, ServerEventType.DONE)

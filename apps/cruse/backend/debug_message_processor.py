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

import queue
from time import time
from typing import Any

from neuro_san.internals.messages.chat_message_type import ChatMessageType
from neuro_san.internals.messages.origination import Origination
from neuro_san.message_processing.message_processor import MessageProcessor


class DebugMessageProcessor(MessageProcessor):
    """Captures inter-agent messages into a thread-safe queue for real-time debug streaming."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()

    def reset(self):
        """Clear any buffered entries (called at the start of each process_once cycle)."""
        # Do NOT clear — we want to keep entries across the processing cycle
        # so the async keepalive loop can drain them incrementally.

    def process_message(self, chat_message_dict: dict[str, Any], message_type: ChatMessageType):
        """Extract agent trace info from the message and enqueue it.

        :param chat_message_dict: The ChatMessage dictionary to process.
        :param message_type: The ChatMessageType of the message.
        """
        text = chat_message_dict.get("text")
        structure = chat_message_dict.get("structure")
        if text is None and structure is None:
            return

        origin = chat_message_dict.get("origin")
        origin_str = ""
        agent_name = ""
        if origin:
            try:
                origin_str = Origination.get_full_name_from_origin(origin)
            except (ValueError, TypeError):
                origin_str = ""
            # The last element in origin is the immediate sender
            if isinstance(origin, list) and len(origin) > 0:
                last = origin[-1]
                if isinstance(last, dict):
                    agent_name = last.get("tool", "")

        response_type = chat_message_dict.get("type")
        resolved_type = ChatMessageType.from_response_type(response_type) if response_type else message_type
        type_str = ChatMessageType.to_string(resolved_type)

        entry = {
            "timestamp": time(),
            "agent": agent_name,
            "origin": origin_str,
            "type": type_str,
            "text": text or "",
            "has_structure": structure is not None,
        }
        self._queue.put_nowait(entry)

    def drain(self) -> list[dict]:
        """Thread-safe bulk dequeue of all buffered entries.

        :return: List of trace entry dicts.
        """
        entries = []
        while True:
            try:
                entries.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return entries

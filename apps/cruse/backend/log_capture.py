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

import collections
import logging
import threading
from time import time


class LogRingBuffer(logging.Handler):
    """A logging handler that buffers records into a fixed-size ring buffer for real-time streaming."""

    def __init__(self, maxlen: int = 500):
        super().__init__()
        self._buffer: collections.deque = collections.deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def emit(self, record: logging.LogRecord):
        """Append a structured log entry to the ring buffer.

        :param record: The log record to capture.
        """
        entry = {
            "timestamp": time(),
            "level": record.levelname,
            "logger": record.name,
            "message": self.format(record),
        }
        with self._lock:
            self._buffer.append(entry)

    def drain(self) -> list[dict]:
        """Return and clear all buffered entries.

        :return: List of log entry dicts.
        """
        with self._lock:
            entries = list(self._buffer)
            self._buffer.clear()
        return entries

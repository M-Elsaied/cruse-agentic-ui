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

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Return the module-level Fernet instance, creating it lazily from FERNET_KEY."""
    global _fernet  # noqa: PLW0603
    if _fernet is None:
        key = os.environ.get("FERNET_KEY", "")
        if not key:
            raise RuntimeError("FERNET_KEY environment variable is not set")
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_key(plaintext: str, *, fernet: Fernet | None = None) -> str:
    """Encrypt a plaintext API key and return the Fernet token as a string.

    :param plaintext: The raw API key to encrypt.
    :param fernet: Optional Fernet instance (for testing). Uses module default if None.
    :return: Base64-encoded Fernet token string.
    """
    f = fernet or _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_key(ciphertext: str, *, fernet: Fernet | None = None) -> str:
    """Decrypt a Fernet token and return the plaintext API key.

    :param ciphertext: The Fernet token string to decrypt.
    :param fernet: Optional Fernet instance (for testing). Uses module default if None.
    :return: The original plaintext API key.
    :raises cryptography.fernet.InvalidToken: If decryption fails.
    """
    f = fernet or _get_fernet()
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def reset_fernet() -> None:
    """Reset the cached Fernet instance. Useful for testing."""
    global _fernet  # noqa: PLW0603
    _fernet = None


__all__ = ["InvalidToken", "decrypt_key", "encrypt_key", "reset_fernet"]

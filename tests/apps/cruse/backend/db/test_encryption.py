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

import pytest
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

from apps.cruse.backend.db.encryption import decrypt_key
from apps.cruse.backend.db.encryption import encrypt_key


@pytest.fixture
def fernet_key():
    return Fernet(Fernet.generate_key())


@pytest.fixture
def fernet_key_b():
    return Fernet(Fernet.generate_key())


def test_round_trip(fernet_key):
    plaintext = "sk-test-1234567890abcdef"
    encrypted = encrypt_key(plaintext, fernet=fernet_key)
    assert encrypted != plaintext
    decrypted = decrypt_key(encrypted, fernet=fernet_key)
    assert decrypted == plaintext


def test_wrong_key_fails(fernet_key, fernet_key_b):
    encrypted = encrypt_key("sk-secret", fernet=fernet_key)
    with pytest.raises(InvalidToken):
        decrypt_key(encrypted, fernet=fernet_key_b)


def test_empty_string(fernet_key):
    encrypted = encrypt_key("", fernet=fernet_key)
    assert decrypt_key(encrypted, fernet=fernet_key) == ""


def test_unicode(fernet_key):
    plaintext = "sk-tëst-ünïcödé-键"
    encrypted = encrypt_key(plaintext, fernet=fernet_key)
    assert decrypt_key(encrypted, fernet=fernet_key) == plaintext


def test_long_key(fernet_key):
    plaintext = "sk-" + "a" * 10000
    encrypted = encrypt_key(plaintext, fernet=fernet_key)
    assert decrypt_key(encrypted, fernet=fernet_key) == plaintext


def test_invalid_token(fernet_key):
    with pytest.raises(InvalidToken):
        decrypt_key("not-a-valid-fernet-token", fernet=fernet_key)

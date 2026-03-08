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

# pylint: disable=missing-function-docstring

import os
from unittest.mock import MagicMock

import pytest

from apps.cruse.backend import network_materializer

HOCON = "{ llm_config { class_name = ChatOpenAI } }"


@pytest.fixture(autouse=True)
def _use_tmp_dir(tmp_path, monkeypatch):
    """Redirect all materializer paths to a temp directory."""
    registries = tmp_path / "registries"
    generated = registries / "generated"
    generated.mkdir(parents=True)
    manifest = generated / "manifest.hocon"
    manifest.write_text("{\n}\n")

    monkeypatch.setattr(network_materializer, "REGISTRIES_DIR", str(registries))
    monkeypatch.setattr(network_materializer, "GENERATED_DIR", str(generated))
    monkeypatch.setattr(network_materializer, "GENERATED_MANIFEST", str(manifest))


def _make_network(created_by="user_2abc1234", slug="my_agent"):
    net = MagicMock()
    net.created_by = created_by
    net.slug = slug
    net.hocon_content = HOCON
    return net


def test_materialize_writes_file():
    net = _make_network()
    path = network_materializer.materialize(net)
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as fh:
        assert fh.read() == HOCON


def test_materialize_registers_in_manifest():
    net = _make_network()
    network_materializer.materialize(net)
    with open(network_materializer.GENERATED_MANIFEST, encoding="utf-8") as fh:
        content = fh.read()
    assert "2abc1234_my_agent.hocon" in content


def test_dematerialize_removes_file():
    net = _make_network()
    path = network_materializer.materialize(net)
    assert os.path.exists(path)
    network_materializer.dematerialize(net.created_by, net.slug)
    assert not os.path.exists(path)


def test_dematerialize_unregisters_from_manifest():
    net = _make_network()
    network_materializer.materialize(net)
    network_materializer.dematerialize(net.created_by, net.slug)
    with open(network_materializer.GENERATED_MANIFEST, encoding="utf-8") as fh:
        content = fh.read()
    assert "2abc1234_my_agent" not in content


def test_materialize_idempotent():
    net = _make_network()
    network_materializer.materialize(net)
    network_materializer.materialize(net)
    with open(network_materializer.GENERATED_MANIFEST, encoding="utf-8") as fh:
        content = fh.read()
    assert content.count("2abc1234_my_agent") == 1


def test_naming_convention():
    key = network_materializer.network_key("user_2abc1234", "travel_bot")
    assert key == "generated/2abc1234_travel_bot"

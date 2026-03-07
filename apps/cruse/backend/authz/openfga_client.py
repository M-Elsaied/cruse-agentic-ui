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

# pylint: disable=import-error
# openfga-sdk is installed via apps/cruse/backend/requirements.txt,
# not the top-level requirements.txt used by CI lint.

import json
import logging
import os

from openfga_sdk import ClientConfiguration
from openfga_sdk.client.client import OpenFgaClient
from openfga_sdk.client.models.check_request import ClientCheckRequest
from openfga_sdk.client.models.list_objects_request import ClientListObjectsRequest
from openfga_sdk.client.models.tuple import ClientTuple
from openfga_sdk.client.models.write_request import ClientWriteRequest
from openfga_sdk.credentials import CredentialConfiguration
from openfga_sdk.credentials import Credentials
from openfga_sdk.exceptions import ValidationException
from openfga_sdk.models.create_store_request import CreateStoreRequest
from openfga_sdk.models.write_authorization_model_request import WriteAuthorizationModelRequest

logger = logging.getLogger(__name__)


class CruseOpenFGAClient:
    """Async OpenFGA client wrapper for CRUSE authorization.

    Manages store creation, authorization model loading, and provides
    high-level check/grant/revoke/list_objects operations.
    """

    def __init__(
        self,
        api_url: str | None = None,
        store_name: str | None = None,
        policy_file: str | None = None,
    ):
        self._api_url = api_url or os.environ.get("FGA_API_URL", "http://localhost:8080")
        self._store_name = store_name or os.environ.get("FGA_STORE_NAME", "cruse")
        self._policy_file = policy_file or os.environ.get(
            "FGA_POLICY_FILE", "plugins/authorization/openfga/sample_authorization_model.json"
        )
        self._store_id: str | None = None
        self._model_id: str | None = None
        self._client: OpenFgaClient | None = None

    def _build_client(self, store_id: str | None = None, model_id: str | None = None) -> OpenFgaClient:
        """Create an OpenFgaClient with the current configuration."""
        api_token = os.environ.get("FGA_API_TOKEN")
        credentials = None
        if api_token:
            credentials = Credentials(
                method="api_token",
                configuration=CredentialConfiguration(api_token=api_token),
            )
        configuration = ClientConfiguration(
            api_url=self._api_url,
            store_id=store_id or "",
            authorization_model_id=model_id or "",
            credentials=credentials,
        )
        return OpenFgaClient(configuration)

    async def init(self) -> None:
        """Initialize: find or create store, load authorization model.

        Call once during application startup.
        """
        await self._ensure_store()
        await self._ensure_model()
        # Build the long-lived client with store + model IDs
        self._client = self._build_client(self._store_id, self._model_id)
        logger.info(
            "OpenFGA initialized (store=%s, model=%s, url=%s)",
            self._store_id,
            self._model_id,
            self._api_url,
        )

    async def close(self) -> None:
        """Close the underlying client connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    @property
    def is_initialized(self) -> bool:
        """True if init() completed successfully."""
        return self._client is not None

    async def _ensure_store(self) -> None:
        """Find the CRUSE store by name, or create it."""
        client = self._build_client()
        try:
            response = await client.list_stores()
            for store in response.stores or []:
                if store.name == self._store_name:
                    self._store_id = store.id
                    logger.info("Found existing OpenFGA store: %s (%s)", self._store_name, self._store_id)
                    return

            # Store not found — create it
            create_resp = await client.create_store(CreateStoreRequest(name=self._store_name))
            self._store_id = create_resp.id
            logger.info("Created OpenFGA store: %s (%s)", self._store_name, self._store_id)
        finally:
            await client.close()

    async def _ensure_model(self) -> None:
        """Load the authorization model from the policy file into the store."""
        if not self._store_id:
            raise RuntimeError("Store must be created before loading model")

        client = self._build_client(self._store_id)
        try:
            # Check for existing models
            response = await client.read_authorization_models()
            if response.authorization_models:
                self._model_id = response.authorization_models[0].id
                logger.info("Using existing authorization model: %s", self._model_id)
                return

            # No model — load from policy file
            policy = self._load_policy_file()
            request = WriteAuthorizationModelRequest(
                type_definitions=policy.get("type_definitions"),
                schema_version=policy.get("schema_version"),
                conditions=policy.get("conditions"),
            )
            write_resp = await client.write_authorization_model(request)
            self._model_id = write_resp.authorization_model_id
            logger.info("Wrote authorization model: %s", self._model_id)
        finally:
            await client.close()

    def _load_policy_file(self) -> dict:
        """Read the authorization model JSON from disk."""
        with open(self._policy_file, encoding="utf-8") as f:
            return json.load(f)

    def _require_client(self) -> OpenFgaClient:
        """Return the initialized client or raise."""
        if self._client is None:
            raise RuntimeError("OpenFGA client not initialized. Call init() first.")
        return self._client

    async def check(self, user_id: str, relation: str, object_type: str, object_id: str) -> bool:
        """Check if a user has a relation on an object.

        :param user_id: The user identifier (without "User:" prefix).
        :param relation: The relation to check (e.g. "read", "update", "delete").
        :param object_type: The object type (e.g. "Organization", "AgentNetwork").
        :param object_id: The object identifier.
        :return: True if the user has the relation on the object.
        """
        client = self._require_client()
        request = ClientCheckRequest(
            user=f"User:{user_id}",
            relation=relation,
            object=f"{object_type}:{object_id}",
        )
        response = await client.check(request)
        return response.allowed

    async def grant(self, user: str, relation: str, object_type: str, object_id: str) -> bool:
        """Write a relationship tuple (grant access).

        :param user: Full user string (e.g. "User:alice" or "User:*").
        :param relation: The relation (e.g. "owner", "tourist").
        :param object_type: The object type.
        :param object_id: The object identifier.
        :return: True if the tuple was written, False if it already existed.
        """
        client = self._require_client()
        client_tuple = ClientTuple(
            user=user,
            relation=relation,
            object=f"{object_type}:{object_id}",
        )
        try:
            await client.write(ClientWriteRequest(writes=[client_tuple]))
            return True
        except ValidationException as exc:
            if "already existed" in str(exc):
                return False
            raise

    async def revoke(self, user: str, relation: str, object_type: str, object_id: str) -> bool:
        """Delete a relationship tuple (revoke access).

        :param user: Full user string (e.g. "User:alice").
        :param relation: The relation to revoke.
        :param object_type: The object type.
        :param object_id: The object identifier.
        :return: True if the tuple was deleted, False if it didn't exist.
        """
        client = self._require_client()
        client_tuple = ClientTuple(
            user=user,
            relation=relation,
            object=f"{object_type}:{object_id}",
        )
        try:
            await client.write(ClientWriteRequest(deletes=[client_tuple]))
            return True
        except ValidationException as exc:
            if "did not exist" in str(exc):
                return False
            raise

    async def list_objects(self, user_id: str, relation: str, object_type: str) -> list[str]:
        """List all objects a user has a relation on.

        :param user_id: The user identifier (without "User:" prefix).
        :param relation: The relation to filter by (e.g. "read").
        :param object_type: The object type (e.g. "AgentNetwork").
        :return: List of object IDs (without type prefix).
        """
        client = self._require_client()
        request = ClientListObjectsRequest(
            user=f"User:{user_id}",
            relation=relation,
            type=object_type,
        )
        response = await client.list_objects(request, {})
        return [obj.split(":", 1)[1] for obj in (response.objects or [])]

    async def grant_org_relation(self, org_id: str, relation: str, object_type: str, object_id: str) -> bool:
        """Write a relationship tuple for an organization member set.

        Used for container relations (e.g. Organization:org1 is container of AgentNetwork:net1).

        :param org_id: The organization identifier.
        :param relation: The relation (e.g. "container").
        :param object_type: The object type.
        :param object_id: The object identifier.
        :return: True if written, False if already existed.
        """
        return await self.grant(f"Organization:{org_id}", relation, object_type, object_id)

    async def grant_org_member_relation(self, org_id: str, relation: str, object_type: str, object_id: str) -> bool:
        """Write a relationship tuple granting org members a relation.

        Uses the Organization#member userset syntax.

        :param org_id: The organization identifier.
        :param relation: The relation to grant (e.g. "tourist").
        :param object_type: The object type.
        :param object_id: The object identifier.
        :return: True if written, False if already existed.
        """
        return await self.grant(f"Organization:{org_id}#member", relation, object_type, object_id)


# Module-level singleton (initialized at startup)
openfga_client = CruseOpenFGAClient()

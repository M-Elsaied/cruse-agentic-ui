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

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.cruse.backend.auth import ClerkUser
from apps.cruse.backend.auth import get_current_user
from apps.cruse.backend.db.engine import get_db
from apps.cruse.backend.db.repositories.agent_network_repo import AgentNetworkRepository
from apps.cruse.backend.models import NetworkCreateRequest
from apps.cruse.backend.models import NetworkDetail
from apps.cruse.backend.models import NetworkInfo
from apps.cruse.backend.models import NetworkListResponse
from apps.cruse.backend.models import NetworkMetadataUpdate
from apps.cruse.backend.models import NetworkUpdateRequest
from apps.cruse.backend.models import NetworkValidateRequest
from apps.cruse.backend.tenant_context import TenantContext
from apps.cruse.backend.tenant_context import get_tenant

router = APIRouter(prefix="/api/networks", tags=["networks"])


async def get_custom_networks_summary(user, db):
    """Load custom networks for /api/systems response."""
    import logging  # pylint: disable=import-outside-toplevel

    try:
        from apps.cruse.backend.network_materializer import network_key  # pylint: disable=import-outside-toplevel
        from apps.cruse.backend.tenant_context import resolve_tenant_context  # pylint: disable=import-outside-toplevel

        tenant = await resolve_tenant_context(user, db)
        repo = AgentNetworkRepository(db)
        owned = await repo.list_owned(tenant.user_id)
        shared = await repo.list_shared(tenant.user_id, tenant.org_id) if tenant.org_id else []

        def to_dict(n):
            return {"name": n.name, "slug": n.slug, "network_path": network_key(n.created_by, n.slug)}

        return {"my_networks": [to_dict(n) for n in owned], "shared_networks": [to_dict(n) for n in shared]}
    except Exception:  # pylint: disable=broad-exception-caught
        logging.getLogger(__name__).exception("Could not load custom networks for /api/systems")
        return {"my_networks": [], "shared_networks": []}


def _ts(value) -> str:
    """Safely convert a datetime to ISO string, handling None."""
    return value.isoformat() if value else ""


def _network_to_info(net) -> NetworkInfo:
    """Convert an AgentNetwork DB record to a NetworkInfo response."""
    from apps.cruse.backend.network_materializer import network_key  # pylint: disable=import-outside-toplevel

    return NetworkInfo(
        id=net.id,
        name=net.name,
        slug=net.slug,
        description=net.description,
        is_shared=net.is_shared,
        network_path=network_key(net.created_by, net.slug),
        created_at=_ts(net.created_at),
        updated_at=_ts(net.updated_at),
    )


def _network_to_detail(net) -> NetworkDetail:
    """Convert an AgentNetwork DB record to a NetworkDetail response."""
    from apps.cruse.backend.network_materializer import network_key  # pylint: disable=import-outside-toplevel

    return NetworkDetail(
        id=net.id,
        name=net.name,
        slug=net.slug,
        description=net.description,
        hocon_content=net.hocon_content,
        is_shared=net.is_shared,
        network_path=network_key(net.created_by, net.slug),
        created_at=_ts(net.created_at),
        updated_at=_ts(net.updated_at),
    )


@router.get("", response_model=NetworkListResponse)
async def list_networks(
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List the user's own networks and networks shared with their org."""
    repo = AgentNetworkRepository(db)
    owned = await repo.list_owned(tenant.user_id)
    shared = await repo.list_shared(tenant.user_id, tenant.org_id) if tenant.org_id else []
    return NetworkListResponse(
        my_networks=[_network_to_info(n) for n in owned],
        shared_networks=[_network_to_info(n) for n in shared],
    )


@router.post("", status_code=201)
async def create_network(
    body: NetworkCreateRequest,
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom agent network."""
    import logging  # pylint: disable=import-outside-toplevel

    from apps.cruse.backend import network_materializer  # pylint: disable=import-outside-toplevel
    from apps.cruse.backend import network_validator  # pylint: disable=import-outside-toplevel

    log = logging.getLogger(__name__)
    repo = AgentNetworkRepository(db)

    # Validate slug
    slug_errors = network_validator.validate_slug(body.slug)
    if slug_errors:
        raise HTTPException(status_code=422, detail=slug_errors[0])

    # Check limit
    count = await repo.count_for_user(tenant.user_id)
    if count >= AgentNetworkRepository.MAX_NETWORKS_PER_USER:
        raise HTTPException(status_code=400, detail=f"Maximum of {repo.MAX_NETWORKS_PER_USER} networks per user")

    # Check duplicate slug
    existing = await repo.get_by_slug(tenant.user_id, body.slug)
    if existing:
        raise HTTPException(status_code=400, detail=f"You already have a network with slug '{body.slug}'")

    # Validate HOCON
    hocon_errors = network_validator.validate_hocon(body.hocon_content)
    if hocon_errors:
        raise HTTPException(status_code=422, detail=hocon_errors[0])

    # repo.create() already flushes internally — refresh to load server defaults
    try:
        net = await repo.create(
            created_by=tenant.user_id,
            name=body.name,
            slug=body.slug,
            hocon_content=body.hocon_content,
            org_id=tenant.org_id,
            description=body.description,
        )
        await db.refresh(net)
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail=f"A network with slug '{body.slug}' already exists") from exc
    log.info("Created network id=%s slug=%s for user=%s", net.id, net.slug, tenant.user_id)

    # Materialize to disk + invalidate caches
    try:
        network_materializer.materialize(net)
        await repo.set_materialized(net.id)
        network_materializer.invalidate_caches()
    except Exception:  # pylint: disable=broad-exception-caught
        log.exception("Failed to materialize network %s — DB record saved but file not written", net.slug)

    # Re-fetch after all DB operations — flush() inside set_materialized expires ORM attributes
    net = await repo.get_by_id(net.id)
    return _network_to_detail(net)


@router.post("/validate")
async def validate_network(
    body: NetworkValidateRequest,
    _user: ClerkUser = Depends(get_current_user),
):
    """Validate HOCON content without saving."""
    from apps.cruse.backend import network_validator  # pylint: disable=import-outside-toplevel

    errors = network_validator.validate_hocon(body.hocon_content)
    return {"valid": len(errors) == 0, "errors": errors}


@router.get("/{network_id}")
async def get_network(
    network_id: int,
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get full network detail (owner or shared)."""
    repo = AgentNetworkRepository(db)
    accessible = await repo.is_accessible(network_id, tenant.user_id, tenant.org_id)
    if not accessible:
        raise HTTPException(status_code=404, detail="Network not found")
    net = await repo.get_by_id(network_id)
    if net is None:
        raise HTTPException(status_code=404, detail="Network not found")
    return _network_to_detail(net)


@router.put("/{network_id}")
async def update_network(
    network_id: int,
    body: NetworkUpdateRequest,
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update network HOCON content. Owner only."""
    import logging  # pylint: disable=import-outside-toplevel

    from apps.cruse.backend import network_materializer  # pylint: disable=import-outside-toplevel
    from apps.cruse.backend import network_validator  # pylint: disable=import-outside-toplevel

    log = logging.getLogger(__name__)
    repo = AgentNetworkRepository(db)
    net = await repo.get_by_id(network_id)
    if net is None or net.created_by != tenant.user_id:
        raise HTTPException(status_code=404, detail="Network not found")

    hocon_errors = network_validator.validate_hocon(body.hocon_content)
    if hocon_errors:
        raise HTTPException(status_code=422, detail=hocon_errors[0])

    await repo.update_content(network_id, body.hocon_content, name=body.name)
    net = await repo.get_by_id(network_id)

    try:
        network_materializer.materialize(net)
        await repo.set_materialized(net.id)
        network_materializer.invalidate_caches()
    except Exception:  # pylint: disable=broad-exception-caught
        log.exception("Failed to materialize network %s after update", net.slug)

    # Re-fetch after all DB operations — flush() inside set_materialized expires ORM attributes
    net = await repo.get_by_id(net.id)
    return _network_to_detail(net)


@router.patch("/{network_id}")
async def patch_network(
    network_id: int,
    body: NetworkMetadataUpdate,
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update network metadata (description, sharing). Owner only."""
    repo = AgentNetworkRepository(db)
    net = await repo.get_by_id(network_id)
    if net is None or net.created_by != tenant.user_id:
        raise HTTPException(status_code=404, detail="Network not found")

    kwargs = {}
    if body.description is not None:
        kwargs["description"] = body.description
    if body.is_shared is not None:
        kwargs["is_shared"] = body.is_shared
    await repo.update_metadata(network_id, **kwargs)

    net = await repo.get_by_id(network_id)
    return _network_to_info(net)


@router.delete("/{network_id}")
async def delete_network(
    network_id: int,
    tenant: TenantContext = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Archive (soft-delete) a network. Owner only."""
    import logging  # pylint: disable=import-outside-toplevel

    from apps.cruse.backend import network_materializer  # pylint: disable=import-outside-toplevel

    log = logging.getLogger(__name__)
    repo = AgentNetworkRepository(db)
    net = await repo.get_by_id(network_id)
    if net is None or net.created_by != tenant.user_id:
        raise HTTPException(status_code=404, detail="Network not found")

    created_by = net.created_by
    slug = net.slug
    await repo.archive(network_id)

    try:
        network_materializer.dematerialize(created_by, slug)
        network_materializer.invalidate_caches()
    except Exception:  # pylint: disable=broad-exception-caught
        log.exception("Failed to dematerialize network %s/%s", created_by, slug)

    return {"status": "archived", "network_id": network_id}

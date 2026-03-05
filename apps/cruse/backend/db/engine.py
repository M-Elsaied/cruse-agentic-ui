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
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)

DEFAULT_DATABASE_URL = "postgresql+asyncpg://cruse:cruse@localhost:5432/cruse"

_engine = None  # pylint: disable=invalid-name
_session_factory: async_sessionmaker[AsyncSession] | None = None  # pylint: disable=invalid-name


async def init_db() -> None:
    """Create the async engine and session factory.

    Call once during application startup.
    """
    global _engine, _session_factory  # noqa: PLW0603  # pylint: disable=global-statement

    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    pool_size = int(os.environ.get("DB_POOL_SIZE", "5"))
    max_overflow = int(os.environ.get("DB_MAX_OVERFLOW", "10"))

    _engine = create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info("Database engine initialized (pool_size=%d, max_overflow=%d)", pool_size, max_overflow)


async def dispose_db() -> None:
    """Dispose of the engine, closing all pooled connections.

    Call once during application shutdown.
    """
    global _engine, _session_factory  # noqa: PLW0603  # pylint: disable=global-statement

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine disposed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Usage::

        @app.get("/api/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    """Return the session factory for use outside of FastAPI dependency injection."""
    return _session_factory

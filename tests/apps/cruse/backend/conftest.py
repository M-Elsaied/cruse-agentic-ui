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

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

# Import all models so metadata is fully populated
import apps.cruse.backend.db.models  # noqa: F401  # pylint: disable=unused-import
from apps.cruse.backend.db.base import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://cruse:cruse@localhost:5432/cruse_test",
)


@pytest_asyncio.fixture
async def engine():
    """Create an async engine for each test. Tables are created once and
    each test's transaction is rolled back, so there is no cross-test pollution.

    Skips the test if PostgreSQL is not reachable or asyncpg is not installed.
    """
    try:
        eng = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        pytest.skip(f"PostgreSQL not available: {exc}")
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine):  # pylint: disable=redefined-outer-name
    """Each test gets a session wrapped in a transaction that rolls back."""
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()

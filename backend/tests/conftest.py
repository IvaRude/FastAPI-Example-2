import asyncio
import os
import pathlib
import sys
import warnings
from typing import AsyncGenerator

import alembic
import pytest
from alembic.config import Config
from asgi_lifespan import LifespanManager
from databases import Database
from fastapi import FastAPI
from httpx import AsyncClient

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from backend.app.api.server import get_application
from backend.app.db.repositories.cleanings import CleaningsRepository
from backend.app.models.cleanings import CleaningInDB, CleaningCreate


# Apply migrations at beginning and end of testing session
@pytest.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")

    alembic.command.upgrade(config, "head")


# Create a new application for testing
@pytest.fixture(scope='session')
def app(apply_migrations: None) -> FastAPI:
    return get_application()


# Grab a reference to our database when needed
@pytest.fixture(scope='session')
def db(app: FastAPI) -> Database:
    return app.state._db


# Make requests in our tests
@pytest.fixture(scope='session')
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with LifespanManager(app):
        async with AsyncClient(
                app=app,
                base_url="http://testserver",
                headers={"Content-Type": "application/json"}
        ) as client:
            yield client


# SETUP
@pytest.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def test_cleaning(db: Database) -> CleaningInDB:
    cleaning_repo = CleaningsRepository(db)
    new_cleaning = CleaningCreate(
        name="fake cleaning name",
        description="fake cleaning description",
        price=9.99,
        cleaning_type="spot_clean",
    )
    return await cleaning_repo.create_cleaning(new_cleaning=new_cleaning)

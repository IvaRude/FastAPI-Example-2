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
from backend.app.models.cleaning import CleaningInDB, CleaningCreate
from backend.app.db.repositories.users import UsersRepository
from backend.app.models.user import UserInDB, UserCreate
from backend.app.core.config import SECRET_KEY, JWT_TOKEN_PREFIX
from backend.app.services import auth_service


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


@pytest.fixture()
async def test_user(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="lebron@james.io",
        username="lebronjames",
        password="heatcavslakers",
    )
    user_repo = UsersRepository(db)
    existing_user = await user_repo.get_user_by_email(email=new_user.email)
    if existing_user:
        return existing_user
    return await user_repo.register_new_user(new_user=new_user)


@pytest.fixture
def authorized_client(client: AsyncClient, test_user: UserInDB) -> AsyncClient:
    access_token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
    client.headers = {
        **client.headers,
        "Authorization": f"{JWT_TOKEN_PREFIX} {access_token}",
    }
    return client

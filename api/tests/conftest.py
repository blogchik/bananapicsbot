import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# 1. Mock the DB Session module BEFORE importing app.main
# This prevents create_engine() from running and failing/hanging
mock_db_session_module = MagicMock()
mock_db_session_module.SessionLocal = MagicMock()
sys.modules["app.db.session"] = mock_db_session_module

# 2. Mock 'app.deps.db' init/shutdown to avoid startup logic
mock_deps_db = MagicMock()
mock_deps_db.init_database = AsyncMock()
mock_deps_db.shutdown_database = AsyncMock()
mock_deps_db.db_session_dep = MagicMock()
# We need db_session_dep to be importable for overrides, but we can also just use the string key
# However, app.main imports init_database from app.deps.db, so it must be mocked.

# But wait, we need to import app.main, which imports app.deps.db.
# If I mock app.db.session, then app.deps.db can import it fine (it gets a mock).
# But App imports init_database.

# Let's import app now
from app.deps.db import db_session_dep
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def mock_db_session():
    """Returns a magic mock that mimics an AsyncSession/Session."""
    session = MagicMock()
    # Mock execute results
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    execute_result.scalar_one.return_value = 0
    execute_result.scalars.return_value.all.return_value = []
    session.execute.return_value = execute_result

    session.commit = MagicMock()
    session.flush = MagicMock()

    def refresh_side_effect(obj, attribute_names=None, with_for_update=None):
        if not getattr(obj, "id", None):
            obj.id = 1
        if not getattr(obj, "created_at", None):
            from datetime import datetime

            obj.created_at = datetime.utcnow()
        if not getattr(obj, "updated_at", None):
            from datetime import datetime

            obj.updated_at = datetime.utcnow()
        if hasattr(obj, "public_id") and not getattr(obj, "public_id", None):
            obj.public_id = "test-uuid"

    session.refresh = MagicMock(side_effect=refresh_side_effect)
    session.add = MagicMock()
    return session


@pytest.fixture
def client(mock_db_session):
    """
    Test client with mocked database session.
    Overrides the db_session_dep dependency.
    """
    # Override the startup/shutdown handlers to plain AsyncMocks if they aren't already
    # (Since we imported app after mocking sys.modules, app.deps.db might be real,
    # but it imports mocked app.db.session. So init_database calling Database.get_engine might still be an issue)

    # Let's patch app.deps.db.init_database using app.dependency_overrides? No, that's for dependencies.
    # We should patch the functions in the module.

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.deps.db.init_database", AsyncMock())
        mp.setattr("app.deps.db.shutdown_database", AsyncMock())

        # Also mock Database.get_engine if needed?
        # app.deps.db refers to app.infrastructure.database.session.Database
        # We might need to mock that too if init_database was not successfully patched above before startup

        app.dependency_overrides[db_session_dep] = lambda: mock_db_session
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()

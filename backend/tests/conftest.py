"""
pytest configuration.

Isolates the test suite from the production SQLite database so integration tests
no longer pollute `nexus_forge.db` with throwaway orgs/connectors/events.

The DATABASE_URL env var is set BEFORE any app module (and thus the `settings`
object / SQLAlchemy engine) is imported, pointing at a dedicated temp SQLite DB.

Note: Qdrant memory is a live cloud sponsor store and is intentionally shared by
tests (real vector writes) — this only isolates the relational SQLite store.
"""
import os
import sys
import tempfile

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# Point the app at a dedicated test database before any app module import.
TEST_DB_DIR = tempfile.mkdtemp(prefix="nexus_test_db_")
_TEST_DB_PATH = os.path.join(TEST_DB_DIR, "test_nexus_forge.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH.replace(os.sep, '/')}"


def pytest_sessionstart(session):
    """Create the test schema once for the whole session."""
    import asyncio
    from app.db.session import init_db, settings as sess_settings

    # Importing the models module registers all mapped classes on Base.metadata,
    # which is required for create_all to build every table.
    from app.db import models  # noqa: F401

    asyncio.run(init_db())

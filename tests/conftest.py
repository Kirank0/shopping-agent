"""
Shared test setup.

src/setup_db.py and src/reviews_api.py read DB_PATH when they are imported, so the
environment must point at a throwaway database *before* any project module is imported.
That is why this happens at module level here rather than in a fixture.
"""

import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

import pytest
from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Keep the real key (environment or .env) for the opt-in live tests, then replace it with a
# dummy so no ordinary test can ever reach the real Groq API.
REAL_GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or dotenv_values(PROJECT_ROOT / ".env").get("GROQ_API_KEY") or ""
os.environ["GROQ_API_KEY"] = "test-dummy-key"

TEST_DB_PATH = os.path.join(tempfile.mkdtemp(prefix="shopping-agent-tests-"), "store.db")
os.environ["DB_PATH"] = TEST_DB_PATH

import setup_db  # noqa: E402


def reset_database() -> None:
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    setup_db.create_database()


@pytest.fixture
def fresh_db() -> str:
    """A newly seeded database (products, reviews, empty orders) for each test."""
    reset_database()
    return TEST_DB_PATH


@pytest.fixture
def db_rows():
    """Run a query against the test database and return the rows as dicts."""

    def query(sql: str, params: tuple = ()) -> list[dict]:
        with closing(sqlite3.connect(TEST_DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    return query

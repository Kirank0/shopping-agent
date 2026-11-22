"""Integration tests for database creation and seeding."""

import setup_db


def test_create_database_builds_and_seeds_tables(fresh_db, db_rows):
    tables = {r["name"] for r in db_rows("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"products", "reviews", "orders"} <= tables

    assert db_rows("SELECT COUNT(*) AS n FROM products")[0]["n"] == 32
    assert db_rows("SELECT COUNT(*) AS n FROM reviews")[0]["n"] > 32
    assert db_rows("SELECT COUNT(*) AS n FROM orders")[0]["n"] == 0


def test_every_product_has_reviews(fresh_db, db_rows):
    unreviewed = db_rows("SELECT id FROM products WHERE id NOT IN (SELECT product_id FROM reviews)")
    assert unreviewed == []


def test_create_database_is_idempotent(fresh_db, db_rows):
    setup_db.create_database()

    assert db_rows("SELECT COUNT(*) AS n FROM products")[0]["n"] == 32
    # Reviews are cleared and re-inserted, never duplicated.
    first_count = db_rows("SELECT COUNT(*) AS n FROM reviews")[0]["n"]
    setup_db.create_database()
    assert db_rows("SELECT COUNT(*) AS n FROM reviews")[0]["n"] == first_count

"""
Products API — product search, product details with reviews, and order
placement against store.db. These are plain functions; agent.py wraps them
as LangChain tools.
"""

import sqlite3
from contextlib import closing

from reviews_api import DB_PATH, get_ratings_for_products

SORT_OPTIONS = ("rating", "price_low", "price_high")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def list_categories() -> list[str]:
    """Return every distinct product category in the store."""
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    return [r["category"] for r in rows]


def search_products(
    keyword: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    organic_only: bool = False,
    sort_by: str = "rating",
    limit: int = 10,
) -> list[dict]:
    """Filter products and attach their average rating and review count."""
    clauses, params = [], []
    if keyword:
        clauses.append("(name LIKE ? OR description LIKE ?)")
        params += [f"%{keyword}%", f"%{keyword}%"]
    if category:
        clauses.append("category = ?")
        params.append(category.strip().lower())
    if min_price is not None:
        clauses.append("price >= ?")
        params.append(min_price)
    if max_price is not None:
        clauses.append("price <= ?")
        params.append(max_price)
    if organic_only:
        clauses.append("is_organic = 1")

    sql = "SELECT id, name, category, price, description, is_organic FROM products"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)

    with closing(_connect()) as conn:
        rows = conn.execute(sql, params).fetchall()

    ratings = {r["product_id"]: r for r in get_ratings_for_products([row["id"] for row in rows])}
    products = [
        {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "price": row["price"],
            "is_organic": bool(row["is_organic"]),
            "description": row["description"],
            "average_rating": ratings[row["id"]]["average_rating"],
            "review_count": ratings[row["id"]]["review_count"],
        }
        for row in rows
    ]

    if min_rating is not None:
        products = [p for p in products if p["average_rating"] >= min_rating]

    if sort_by == "price_low":
        products.sort(key=lambda p: p["price"])
    elif sort_by == "price_high":
        products.sort(key=lambda p: p["price"], reverse=True)
    else:
        products.sort(key=lambda p: (p["average_rating"], p["review_count"]), reverse=True)

    return products[: max(1, limit)]


def get_product_details(product_id: int) -> dict | None:
    """Return one product with its rating summary and every review, or None."""
    with closing(_connect()) as conn:
        product = conn.execute(
            "SELECT id, name, category, price, description, is_organic FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if product is None:
            return None
        reviews = conn.execute(
            "SELECT reviewer_name, rating, review_text FROM reviews WHERE product_id = ? ORDER BY id",
            (product_id,),
        ).fetchall()

    rating = get_ratings_for_products([product_id])[0]
    return {
        "id": product["id"],
        "name": product["name"],
        "category": product["category"],
        "price": product["price"],
        "is_organic": bool(product["is_organic"]),
        "description": product["description"],
        "average_rating": rating["average_rating"],
        "review_count": rating["review_count"],
        "reviews": [dict(r) for r in reviews],
    }


def place_order(product_id: int) -> dict | None:
    """Insert one order row for the product. Returns the order, or None if the product doesn't exist."""
    with closing(_connect()) as conn:
        product = conn.execute("SELECT id, name, price FROM products WHERE id = ?", (product_id,)).fetchone()
        if product is None:
            return None
        cursor = conn.execute(
            "INSERT INTO orders (product_id, product_name, price) VALUES (?, ?, ?)",
            (product["id"], product["name"], product["price"]),
        )
        conn.commit()
        order = conn.execute(
            "SELECT id, product_id, product_name, price, ordered_at FROM orders WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return dict(order)

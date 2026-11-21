"""
Shopping agent — a LangChain agent running GPT OSS 120B on Groq Cloud, with
tools for searching products, reading reviews and placing orders.
"""

import json
from typing import Literal

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_groq import ChatGroq

import products_api

MODEL_NAME = "openai/gpt-oss-120b"


@tool
def search_products(
    keyword: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    organic_only: bool = False,
    sort_by: Literal["rating", "price_low", "price_high"] = "rating",
    limit: int = 10,
) -> str:
    """Search the store's products. All filters are optional and combine with AND.

    Args:
        keyword: Text matched against product name and description, e.g. "manuka", "almond".
        category: Exact category name from the store's category list.
        min_price: Lowest price in dollars (inclusive).
        max_price: Highest price in dollars (inclusive).
        min_rating: Lowest average rating, 0-5 (inclusive).
        organic_only: True to return only organic products.
        sort_by: "rating" (best first), "price_low" (cheapest first) or "price_high".
        limit: Maximum number of products to return.
    """
    results = products_api.search_products(
        keyword=keyword,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        organic_only=organic_only,
        sort_by=sort_by,
        limit=limit,
    )
    if not results:
        return "No products matched those filters."
    return json.dumps(results)


@tool
def get_product_reviews(product_id: int) -> str:
    """Get a product's details, average rating and every customer review.

    Args:
        product_id: The product's ID (find it with search_products first if you only know the name).
    """
    details = products_api.get_product_details(product_id)
    if details is None:
        return f"No product with ID {product_id} exists."
    return json.dumps(details)


@tool
def place_order(product_id: int) -> str:
    """Place an order for one unit of a product.

    Args:
        product_id: The ID of the product to order.
    """
    order = products_api.place_order(product_id)
    if order is None:
        return f"Order NOT placed: no product with ID {product_id} exists."
    return "Order placed successfully: " + json.dumps(order)


def _system_prompt() -> str:
    categories = ", ".join(products_api.list_categories())
    return f"""You are a friendly shopping assistant for an online natural-foods store.

Store categories (use these exact values for the `category` filter): {categories}.
Map everyday words onto them, for example: "dairy free milk" or "plant milk" -> dairy-alt;
"nuts and seeds" -> search both nuts and seeds. When unsure of the category, use `keyword` instead.

Rules:
- Only use facts returned by your tools. Never invent products, prices, ratings, reviews or orders.
- Ratings are out of 5. "Rating above X" means min_rating = X.
- To summarize reviews, find the product with search_products, then call get_product_reviews.
  Describe the common themes and mention the average rating and number of reviews.
- Ordering: each order is for one unit. If the user gives a product ID, call place_order with it.
  If they name a product, search for it; if exactly one product clearly matches, order it,
  otherwise list the matches with their IDs and ask which one they want.
  Only say an order was placed when place_order reports success, and include the order ID.
- You cannot show order history or cancel orders.
- Be concise. List products as a markdown table with ID, name, price, rating and organic (Yes/No).
"""


def build_agent():
    """Create the agent. Requires the GROQ_API_KEY environment variable."""
    model = ChatGroq(model=MODEL_NAME, temperature=0, max_retries=2)
    return create_agent(
        model,
        tools=[search_products, get_product_reviews, place_order],
        system_prompt=_system_prompt(),
    )

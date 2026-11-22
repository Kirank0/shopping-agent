"""Integration tests for products_api against the real seeded SQLite database."""

import pytest

import products_api


@pytest.fixture(autouse=True)
def _db(fresh_db):
    pass


def ids(products):
    return [p["id"] for p in products]


def test_list_categories():
    assert products_api.list_categories() == [
        "coffee",
        "dairy-alt",
        "grains",
        "honey",
        "nuts",
        "oil",
        "seeds",
        "snacks",
        "tea",
    ]


def test_search_returns_full_product_records():
    product = products_api.search_products(keyword="manuka")[0]

    assert product == {
        "id": 3,
        "name": "Organic Manuka Honey",
        "category": "honey",
        "price": 29.99,
        "is_organic": True,
        "description": "Premium organic Manuka honey from New Zealand",
        "average_rating": 4.83,
        "review_count": 3,
    }


def test_keyword_matches_name_and_description():
    assert ids(products_api.search_products(keyword="Manuka")) == [3]
    # "omega-3" appears only in descriptions
    assert set(ids(products_api.search_products(keyword="omega-3"))) == {11, 15}


def test_category_is_normalised():
    results = products_api.search_products(category="  HONEY ", limit=50)
    assert len(results) == 8
    assert {p["category"] for p in results} == {"honey"}


def test_price_range_is_inclusive():
    results = products_api.search_products(min_price=8.99, max_price=9.99, limit=50)
    assert results
    assert all(8.99 <= p["price"] <= 9.99 for p in results)
    assert {4, 14, 22, 25} <= set(ids(results))


def test_organic_only():
    results = products_api.search_products(organic_only=True, limit=50)
    assert results
    assert all(p["is_organic"] for p in results)


def test_min_rating():
    results = products_api.search_products(min_rating=4.75, limit=50)
    assert results
    assert all(p["average_rating"] >= 4.75 for p in results)


def test_combined_filters_example_question():
    # "Find me organic honey under $20 with ratings above 4.5"
    results = products_api.search_products(category="honey", max_price=20, min_rating=4.5, organic_only=True)
    assert set(ids(results)) == {1, 5, 7}
    assert results[0]["id"] == 7  # highest rated first


@pytest.mark.parametrize(
    ("sort_by", "key", "reverse"),
    [
        ("rating", lambda p: (p["average_rating"], p["review_count"]), True),
        ("price_low", lambda p: p["price"], False),
        ("price_high", lambda p: p["price"], True),
    ],
)
def test_sort_orders(sort_by, key, reverse):
    results = products_api.search_products(sort_by=sort_by, limit=50)
    assert len(results) == 32
    assert [key(p) for p in results] == sorted((key(p) for p in results), reverse=reverse)


def test_cheapest_dairy_free_milk():
    assert products_api.search_products(category="dairy-alt", sort_by="price_low", limit=1)[0]["name"] == "Soy Milk"


def test_limit_is_at_least_one():
    assert len(products_api.search_products(limit=3)) == 3
    assert len(products_api.search_products(limit=0)) == 1


def test_no_matches():
    assert products_api.search_products(keyword="caviar") == []


def test_product_details_include_reviews():
    details = products_api.get_product_details(3)

    assert details["name"] == "Organic Manuka Honey"
    assert details["average_rating"] == 4.83
    assert details["review_count"] == 3
    assert details["reviews"][0] == {
        "reviewer_name": "Henry",
        "rating": 5.0,
        "review_text": "Worth every penny, incredible quality.",
    }
    assert len(details["reviews"]) == 3


def test_product_details_unknown_id():
    assert products_api.get_product_details(999) is None


def test_place_order_inserts_row(db_rows):
    order = products_api.place_order(13)

    assert order["product_id"] == 13
    assert order["product_name"] == "Organic Almonds"
    assert order["price"] == 11.99
    assert order["ordered_at"]
    assert db_rows("SELECT id, product_id FROM orders") == [{"id": order["id"], "product_id": 13}]


def test_place_order_gives_each_order_a_new_id():
    first = products_api.place_order(1)
    second = products_api.place_order(1)
    assert second["id"] == first["id"] + 1


def test_place_order_unknown_product(db_rows):
    assert products_api.place_order(999) is None
    assert db_rows("SELECT * FROM orders") == []

"""Unit tests for the LangChain tool wrappers in agent.py, with products_api mocked out."""

import json

import pytest

import agent


@pytest.fixture
def fake_api(monkeypatch):
    calls = {}

    def record(name, result):
        def fn(*args, **kwargs):
            calls[name] = (args, kwargs)
            return result

        return fn

    def install(**results):
        for name, result in results.items():
            monkeypatch.setattr(agent.products_api, name, record(name, result))
        return calls

    return install


def test_search_products_returns_json_and_passes_filters(fake_api):
    products = [{"id": 1, "name": "Organic Raw Honey", "price": 14.99}]
    calls = fake_api(search_products=products)

    out = agent.search_products.invoke(
        {"keyword": "honey", "max_price": 20, "min_rating": 4.5, "organic_only": True, "sort_by": "price_low"}
    )

    assert json.loads(out) == products
    _, kwargs = calls["search_products"]
    assert kwargs == {
        "keyword": "honey",
        "category": None,
        "min_price": None,
        "max_price": 20,
        "min_rating": 4.5,
        "organic_only": True,
        "sort_by": "price_low",
        "limit": 10,
    }


def test_search_products_with_no_results(fake_api):
    fake_api(search_products=[])
    assert agent.search_products.invoke({"keyword": "caviar"}) == "No products matched those filters."


def test_search_products_rejects_unknown_sort():
    with pytest.raises(ValueError):
        agent.search_products.invoke({"sort_by": "random"})


def test_get_product_reviews_returns_details(fake_api):
    details = {"id": 3, "name": "Organic Manuka Honey", "reviews": [{"rating": 5.0}]}
    calls = fake_api(get_product_details=details)

    assert json.loads(agent.get_product_reviews.invoke({"product_id": 3})) == details
    assert calls["get_product_details"][0] == (3,)


def test_get_product_reviews_unknown_product(fake_api):
    fake_api(get_product_details=None)
    assert agent.get_product_reviews.invoke({"product_id": 999}) == "No product with ID 999 exists."


def test_place_order_success(fake_api):
    order = {"id": 1, "product_id": 5, "product_name": "Organic Buckwheat Honey", "price": 18.99}
    fake_api(place_order=order)

    out = agent.place_order.invoke({"product_id": 5})

    assert out.startswith("Order placed successfully: ")
    assert json.loads(out.removeprefix("Order placed successfully: ")) == order


def test_place_order_unknown_product(fake_api):
    fake_api(place_order=None)
    assert agent.place_order.invoke({"product_id": 999}) == "Order NOT placed: no product with ID 999 exists."

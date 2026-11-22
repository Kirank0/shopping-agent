"""Integration tests for rating aggregation against the seeded database."""

import pytest

import reviews_api


@pytest.fixture(autouse=True)
def _db(fresh_db):
    pass


def test_single_product_rating():
    # Organic Manuka Honey: 5.0, 4.5, 5.0
    assert reviews_api.get_product_rating(3) == {"product_id": 3, "average_rating": 4.83, "review_count": 3}


def test_unknown_product_has_no_rating():
    assert reviews_api.get_product_rating(999) == {"product_id": 999, "average_rating": 0.0, "review_count": 0}


def test_batch_ratings_keep_input_order_and_fill_missing():
    results = reviews_api.get_ratings_for_products([13, 999, 3])

    assert [r["product_id"] for r in results] == [13, 999, 3]
    assert results[0] == {"product_id": 13, "average_rating": 4.75, "review_count": 4}
    assert results[1] == {"product_id": 999, "average_rating": 0.0, "review_count": 0}
    assert results[2]["average_rating"] == 4.83


def test_batch_ratings_empty_list():
    assert reviews_api.get_ratings_for_products([]) == []

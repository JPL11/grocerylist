"""
Optional challenge 4 — a failing test for bulk purchase.

Sets up a list with 2 already-purchased items and 3 unpurchased ones, then
asserts the three things the PR description actually promises:
  (a) all 5 items end up purchased,
  (b) the call returns 3 (newly purchased), not 5, and
  (c) the 2 originally-purchased items keep their original purchased_by.

This passes against solutions/corrected.py and FAILS against the buggy PR
implementation (which returns 5 and overwrites the original purchasers).
"""

from datetime import datetime, timedelta, timezone

import pytest

from extensions import db
from models import User, GroceryList, Item
from solutions.corrected import purchase_all_items


@pytest.fixture
def list_with_mixed_items(app_ctx):
    now = datetime.now(timezone.utc)
    shopper = User(username="shopper", email="shopper@grocerylist.app")
    original = User(username="original", email="original@grocerylist.app")
    db.session.add_all([shopper, original])
    db.session.flush()

    glist = GroceryList(name="Mixed", created_by=shopper.id)
    db.session.add(glist)
    db.session.flush()

    # 2 already purchased by `original`
    for i in range(2):
        db.session.add(
            Item(
                list_id=glist.id,
                name=f"Bought {i}",
                added_by=original.id,
                is_purchased=True,
                purchased_by=original.id,
                purchased_at=now - timedelta(hours=1),
            )
        )
    # 3 unpurchased
    for i in range(3):
        db.session.add(
            Item(list_id=glist.id, name=f"Todo {i}", added_by=shopper.id)
        )
    db.session.commit()
    return {"list_id": glist.id, "shopper_id": shopper.id, "original_id": original.id}


def test_purchase_all_marks_remaining_counts_newly_and_preserves_attribution(
    list_with_mixed_items,
):
    ctx = list_with_mixed_items
    count = purchase_all_items(ctx["list_id"], ctx["shopper_id"])

    items = Item.query.filter_by(list_id=ctx["list_id"]).all()

    # (a) all 5 end up purchased
    assert all(item.is_purchased for item in items)
    assert len(items) == 5

    # (b) the call reports only what it newly purchased
    assert count == 3

    # (c) the 2 originally-purchased items keep their original purchaser
    originals = [i for i in items if i.name.startswith("Bought")]
    assert len(originals) == 2
    assert all(i.purchased_by == ctx["original_id"] for i in originals)

    # and the 3 newly purchased are attributed to the shopper
    todos = [i for i in items if i.name.startswith("Todo")]
    assert all(i.purchased_by == ctx["shopper_id"] for i in todos)


def test_purchase_all_requires_user_id(list_with_mixed_items):
    with pytest.raises(ValueError):
        purchase_all_items(list_with_mixed_items["list_id"], None)


def test_purchase_all_404s_on_missing_list(app_ctx):
    with pytest.raises(ValueError):
        purchase_all_items("does-not-exist", "some-user")

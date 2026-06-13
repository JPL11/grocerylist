"""
solutions/corrected.py — Optional challenge 1

Corrected implementations of both PR functions, written against the same
contracts the PR descriptions state and modeled on the base app's
`mark_purchased()` (explicit validation, only-touch-valid-state, parity 404s).

Fixes vs. the proposed PRs:

purchase_all_items()
  - validates user_id is present (was unvalidated → None attribution)
  - 404s on a missing list (was silent {"purchased": 0})
  - filters to is_purchased=False, so existing attribution is never overwritten
  - returns the count of NEWLY purchased items (was len of all items)

get_list_stats()
  - 404s on a missing list (was 200 with all-zeros)
  - by_category counts ONLY remaining items, matching the frontend's use case
    ("break down what's remaining by category"); sum(by_category) == remaining
"""

from datetime import datetime, timezone
from extensions import db
from models import GroceryList, Item


def purchase_all_items(list_id: str, user_id: str) -> int:
    """
    Mark all *unpurchased* items in a list as purchased.

    Returns the number of items this call newly purchased. Raises ValueError if
    user_id is missing or the list does not exist.
    """
    if not user_id:
        raise ValueError("Missing required field: user_id")

    grocery_list = db.session.get(GroceryList, list_id)
    if not grocery_list:
        raise ValueError(f"List {list_id!r} not found")

    # Only items not already purchased — never overwrite existing attribution.
    items = Item.query.filter_by(list_id=list_id, is_purchased=False).all()
    now = datetime.now(timezone.utc)
    for item in items:
        item.is_purchased = True
        item.purchased_by = user_id
        item.purchased_at = now
    db.session.commit()

    # Because we filtered to unpurchased, this is exactly the newly-purchased count.
    return len(items)


def get_list_stats(list_id: str) -> dict:
    """
    Compute summary statistics for a grocery list.

    by_category counts only items still remaining (unpurchased), so it can drive
    an in-store "what's left by aisle" view. Raises ValueError if the list does
    not exist.
    """
    grocery_list = db.session.get(GroceryList, list_id)
    if not grocery_list:
        raise ValueError(f"List {list_id!r} not found")

    items = Item.query.filter_by(list_id=list_id).all()
    total = len(items)
    purchased = sum(1 for item in items if item.is_purchased)
    remaining = total - purchased

    by_category = {}
    for item in items:
        if item.is_purchased:
            continue  # remaining-by-category only
        cat = item.category or "uncategorized"
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "list_id": list_id,
        "total_items": total,
        "purchased": purchased,
        "remaining": remaining,
        "by_category": by_category,
    }

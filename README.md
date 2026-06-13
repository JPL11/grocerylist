# 🛒 GroceryList

A shared grocery-list API where members create lists, add items, and track what's been purchased during a shopping trip. Flask + SQLAlchemy in a clean **routes → services → models** layered architecture.

**Status: complete.** This was a code-review lab: two AI-generated pull requests were submitted against a correct base app, and the job was to review them like a senior engineer — read each PR description as a contract, compare it line-by-line against the code, and verify every finding against a running server. **Both PRs were reviewed (5 bugs found, both "Request Changes"), corrected implementations were written, and a regression test locks in the fix.** All four optional challenges are done. Built for AI201 Lab 6.

---

## The Review

Both PRs implement the happy path correctly and break on everything after it — pre-existing data, missing inputs, and the gap between the stated use case and the actual computation. Full write-up with verdicts in [`review_template.md`](review_template.md); corrected code and extensions in [`optional-challenges.md`](optional-challenges.md).

### PR #1 — `POST /lists/<id>/purchase-all` (bulk purchase) → **Request Changes**

| # | Issue | Category | Evidence (verified on `try_prs.py`) |
|---|---|---|---|
| 1 | Query is `filter_by(list_id=...)` — **all** items, not unpurchased — so the loop overwrites `purchased_by`/`purchased_at` on already-bought items | Data corruption | Bulk-buying as **maya** changed leo's Olive Oil attribution from leo → maya, permanently |
| 2 | Returns `len(items)` — the **total** count, not the number newly purchased | Misleading return | Returned `{"purchased": 8}` when only 5 were newly purchased |
| 3 | `user_id` is read with `data.get()` and never validated | Unvalidated input | Empty body `{}` → **HTTP 200**, all items set to `purchased_by: null` (base app returns **400**) |

### PR #2 — `GET /lists/<id>/stats` (list stats) → **Request Changes**

| # | Issue | Category | Evidence |
|---|---|---|---|
| 1 | `by_category` counts **all** items, but the frontend asked for "what's *remaining* by category" for in-store navigation | Semantic mismatch | `sum(by_category) == 8` (total), not `remaining` (5); produce showed 2 when 1 was already in the cart |
| 2 | No existence check — a bad `list_id` returns zeros with `200` | Missing 404 / inconsistency | `GET /lists/bad-id/stats` → **HTTP 200** `{…all zeros}`, while `get_items` returns **404** |

**The pattern:** AI-generated code nails the happy path and misses what comes after it — wrong filter scope on pre-existing data, return values that measure the wrong thing, unvalidated inputs, and computations that are correct in the abstract but wrong for the concrete use case.

---

## Optional Challenges

| # | Challenge | Result |
|---|---|---|
| 1 | **Correct implementation** | [`solutions/corrected.py`](solutions/corrected.py) + runnable [`try_prs_fixed.py`](try_prs_fixed.py): filter to unpurchased, validate `user_id`, 404 parity, and `by_category` over remaining only. Verified end-to-end (count 5, attribution preserved, `sum(by_category)==remaining`, 404/400 correct). |
| 2 | **Blast radius** | Impact analysis of `user_id=None` — anonymizes the whole list's attribution, breaking per-user stats, cost-splitting, audit trails, and FK-joined reports, silently and with no undo. |
| 3 | **Review the reviewer** | PR #1's three issues are really **two** fixes (the unpurchased filter also fixes the count); the `user_id` guard is independent. Documented so fixes target root causes, not symptoms. |
| 4 | **Failing test** | [`tests/test_purchase_all.py`](tests/test_purchase_all.py): asserts all 5 end purchased, the call returns **3**, and the 2 originals keep their purchaser. Fails against the buggy PR, passes against the corrected code. |

---

## Architecture

| Layer | Files | Responsibility |
|---|---|---|
| **Routes** | `routes/lists.py` | Receive HTTP, validate presence, call services, format JSON + status codes |
| **Services** | `services/list_service.py` | Business logic; `mark_purchased()` is the reference implementation (explicit valid/already-done/not-found handling) |
| **Models** | `models.py` | `User`, `GroceryList`, `Item` — `Item` tracks `added_by` vs `purchased_by`, with `is_purchased`/`purchased_at` |

```
POST /lists/<id>/items          → list_service.add_item()
PATCH /lists/<id>/items/<item>  → list_service.mark_purchased()   ← the correctness reference
GET  /lists/<id>/items          → list_service.get_items()         (404 on bad list)

# proposed in the PRs (under review):
POST /lists/<id>/purchase-all   → pr1_bulk_purchase.py   (try_prs.py / try_prs_fixed.py)
GET  /lists/<id>/stats          → pr2_list_stats.py       (try_prs.py / try_prs_fixed.py)
```

### Tech stack

Python 3.12 · Flask 3.1 · Flask-SQLAlchemy 3.1 / SQLAlchemy 2.0 · SQLite · pytest (dev)

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
# or: .venv\Scripts\activate   # Windows

pip install -r requirements.txt

python seed_data.py            # prints user IDs + list IDs
python app.py                  # base app at http://127.0.0.1:5000
```

To exercise the PRs under review (base app + both proposed endpoints):

```bash
python try_prs.py              # the PRs as submitted (buggy)
python try_prs_fixed.py        # the corrected implementations (challenge 1)
```

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q            # 3 passed
```

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/lists/` | List all grocery lists |
| POST | `/lists/` | Create a list |
| GET | `/lists/<list_id>/items` | Items for a list (404 on bad list) |
| POST | `/lists/<list_id>/items` | Add an item |
| PATCH | `/lists/<list_id>/items/<item_id>` | Mark an item purchased |
| POST | `/lists/<list_id>/purchase-all` | *(PR #1, under review)* bulk purchase |
| GET | `/lists/<list_id>/stats` | *(PR #2, under review)* list stats |

---

## Project Structure

```
grocerylist/
├── app.py                      # Flask application factory
├── extensions.py               # SQLAlchemy instance
├── models.py                   # User, GroceryList, Item
├── routes/lists.py             # list + item routes
├── services/list_service.py    # business logic (mark_purchased = reference)
├── prs/                        # the two PRs under review
│   ├── pr1_description.md / pr1_bulk_purchase.py
│   └── pr2_description.md / pr2_list_stats.py
├── try_prs.py                  # base app + PRs as submitted
├── try_prs_fixed.py            # base app + CORRECTED PRs (challenge 1)
├── solutions/corrected.py      # corrected implementations (challenge 1)
├── tests/test_purchase_all.py  # regression test (challenge 4)
├── review_template.md          # the completed code review
├── optional-challenges.md      # challenge write-up
├── seed_data.py                # 2 users, 2 lists, 12 items
├── requirements.txt
└── requirements-dev.txt        # adds pytest
```

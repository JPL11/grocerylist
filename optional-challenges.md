# Lab 6 — Optional Challenges

All four optional challenges are done. The reviews themselves are in
`review_template.md`; this file covers the extensions.

| # | Challenge | Status | Where |
|---|---|---|---|
| 1 | Write a correct implementation | ✅ | `solutions/corrected.py`, runnable via `try_prs_fixed.py` |
| 2 | Estimate the blast radius | ✅ | below |
| 3 | Review the reviewer | ✅ | below |
| 4 | Write a failing test | ✅ | `tests/test_purchase_all.py` |

---

## Challenge 1 — Correct implementation

`solutions/corrected.py` reimplements both functions against the stated
contracts, modeled on the base app's `mark_purchased()`. Run the corrected
endpoints with `python try_prs_fixed.py`.

**`purchase_all_items()`** — validates `user_id` is present (else `ValueError`
→ 400), 404s on a missing list, filters to `is_purchased=False` (so existing
attribution is never overwritten), and returns the **newly-purchased** count.

**`get_list_stats()`** — 404s on a missing list and builds `by_category` from
**unpurchased items only**, so `sum(by_category) == remaining`.

Verified live against the seed data (Weekly Shop, 5 unpurchased + 3 purchased):

| Check | Buggy PR | Corrected |
|---|---|---|
| `stats` → `sum(by_category)` | 8 (= total) | **5 (= remaining)** |
| `stats` on bad list id | 200 + zeros | **404** |
| `purchase-all` missing `user_id` | 200, sets `purchased_by=null` | **400** |
| `purchase-all` count (5 unpurchased) | 8 | **5** |
| leo's already-bought Olive Oil after maya's bulk-buy | overwritten → maya | **preserved → leo** |

---

## Challenge 2 — Blast radius of `user_id = None`

If `purchase-all` is called without a `user_id`, the buggy code marks every item
purchased with `purchased_by = None`. In a shared, multi-user app the immediate
victims are the **other members of that list**: anyone relying on "who bought
what" loses that record for the entire list in a single request, and because the
write also overwrites already-purchased rows, even items correctly attributed to
a real user beforehand are wiped to `None`. Downstream, anything keyed on
`purchased_by` breaks or silently skews — per-user "you bought N items"
contribution stats, fair-share/cost-splitting features, audit trails, and
notifications like "leo bought the milk" all either drop the anonymized rows or
mis-bucket them as belonging to no one. Because `purchased_by` is a foreign key
to `user.id`, the `None` writes also quietly sever the relationship used by any
join over a user's purchases, so reports don't error — they just undercount.
None of this surfaces in testing, since the happy-path response is a clean
`200`; the damage is only visible later, in data that's already corrupted with no
undo.

---

## Challenge 3 — Review the reviewer

Re-checking each suggested fix for "symptom vs. root cause":

- **PR #1, Issue 1 (filter scope).** Fix = query `is_purchased=False`. This is
  the root cause, and it has a bonus: it *also* fixes Issue 2's count, because
  `len(items)` over the filtered set is exactly the newly-purchased number. So
  two reported issues collapse into one change — worth stating explicitly in the
  review so the author doesn't "fix the count" separately and redundantly.
- **PR #1, Issue 3 (missing `user_id`).** This is **independent** — the filter
  fix does nothing for it. A complete fix needs the route-level `400` guard *and*
  (defensively) the service raising on a falsy `user_id`, so the function is safe
  no matter who calls it (the corrected version does both). A reviewer who only
  said "add the filter" would have left the `None`-attribution bug live.
- **PR #2, Issue 1 (semantic mismatch).** Fix = count remaining only. Complete,
  but the *root cause* is conceptual, not mechanical: the field was built from
  the wrong row set relative to the use case. The durable fix is also a naming
  discipline — if an all-items breakdown is ever wanted, it must be a separate,
  explicitly named field, not a silent reinterpretation of `by_category`.
- **PR #2, Issue 2 (missing 404).** Fix = existence check → 404. Root cause, and
  it restores parity with the rest of the API (`get_items`), which is the real
  requirement — not just "return an error."

Net: the only place the first-pass fixes were *incomplete* was treating PR #1's
three issues as three separate fixes. They're really **two** changes (filter +
validation), and the corrected implementation reflects that.

---

## Challenge 4 — Failing test

`tests/test_purchase_all.py` sets up a list with 2 already-purchased items
(bought by `original`) and 3 unpurchased ones, runs `purchase_all_items()`, and
asserts: (a) all 5 end purchased, (b) the call returns **3**, and (c) the 2
original items keep `purchased_by == original`.

```bash
pip install -r requirements-dev.txt   # or: pip install pytest
python -m pytest -q                    # 3 passed (against solutions/corrected.py)
```

The test is a real regression test — run against the **buggy** PR implementation
it fails exactly where the bugs are:

```
(b) returns 5  -> expected 3 : FAIL
(c) originals keep purchaser  : FAIL (attribution overwritten)
```

and passes against `solutions/corrected.py`. Two more tests cover the missing-
`user_id` and missing-list cases.

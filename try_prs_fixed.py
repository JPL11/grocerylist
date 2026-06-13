"""
try_prs_fixed.py — Optional challenge 1 (runnable)

Same as try_prs.py, but wires up the CORRECTED implementations from
solutions/corrected.py, with route-level validation and parity 404s.

Run INSTEAD of app.py / try_prs.py:
    python try_prs_fixed.py

Endpoints behave per the PR contracts:
    POST /lists/<list_id>/purchase-all  → 400 if user_id missing, 404 if list
        missing, otherwise {"purchased": <newly purchased count>}
    GET  /lists/<list_id>/stats         → 404 if list missing; by_category sums
        to remaining
"""

from flask import jsonify, request
from app import create_app
from solutions.corrected import purchase_all_items, get_list_stats

app = create_app()


@app.route("/lists/<list_id>/purchase-all", methods=["POST"])
def purchase_all(list_id):
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing required field: user_id"}), 400
    try:
        count = purchase_all_items(list_id, user_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return jsonify({"purchased": count}), 200


@app.route("/lists/<list_id>/stats", methods=["GET"])
def list_stats(list_id):
    try:
        stats = get_list_stats(list_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return jsonify(stats), 200


if __name__ == "__main__":
    print("GroceryList — PR test mode (CORRECTED implementations)")
    app.run(debug=False, port=5000)

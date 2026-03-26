"""
Omnium Flask REST API
======================

Entry point: flask --app src.omnium.api run
Or:          python -m flask --app src.omnium.api run

All responses are JSON. The WPF desktop app communicates with this API
on localhost:5000.
"""

from flask import Flask, jsonify, request

from src.omnium.data import db
from src.omnium.authentication.auth_system import RegistrationSystem


def create_app() -> Flask:
    """App factory — creates and configures the Flask application."""
    app = Flask(__name__)

    # Shared auth instance (holds no per-request state worth worrying about)
    auth = RegistrationSystem()

    # ── Health Check ──

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    # ── Assets ──

    @app.get("/assets/search")
    def assets_search():
        q = request.args.get("q", "")
        if not q:
            return jsonify({"error": "query parameter 'q' is required"}), 400
        results = db.search_assets(q)
        return jsonify(results)

    @app.get("/assets/<int:asset_id>")
    def assets_get(asset_id: int):
        asset = db.get_asset_by_id(asset_id)
        if not asset:
            return jsonify({"error": "asset not found"}), 404
        return jsonify(asset)

    # ── Prices ──

    @app.get("/prices/<int:asset_id>")
    def prices_history(asset_id: int):
        limit = request.args.get("limit", 30, type=int)
        history = db.get_price_history(asset_id, limit)
        return jsonify(history)

    @app.get("/prices/<int:asset_id>/latest")
    def prices_latest(asset_id: int):
        price = db.get_latest_price(asset_id)
        if not price:
            return jsonify({"error": "no price data found"}), 404
        return jsonify(price)

    # ── Accounts ──

    @app.get("/account/<int:account_id>")
    def account_get(account_id: int):
        account = db.get_account(account_id)
        if not account:
            return jsonify({"error": "account not found"}), 404
        return jsonify(account)

    @app.get("/account/<int:account_id>/trades")
    def account_trades(account_id: int):
        trades = db.get_trades(account_id)
        return jsonify(trades)

    @app.get("/account/<int:account_id>/position/<int:asset_id>")
    def account_position(account_id: int, asset_id: int):
        position = db.get_position(account_id, asset_id)
        return jsonify({"account_id": account_id, "asset_id": asset_id, "shares": position})

    # ── Auth ──

    @app.post("/auth/register")
    def auth_register():
        data = request.get_json()
        if not data or "username" not in data or "password" not in data:
            return jsonify({"error": "username and password are required"}), 400

        success, message = auth.register(data["username"], data["password"])
        status = 201 if success else 400
        return jsonify({"success": success, "message": message}), status

    @app.post("/auth/login")
    def auth_login():
        data = request.get_json()
        if not data or "username" not in data or "password" not in data:
            return jsonify({"error": "username and password are required"}), 400

        success, message = auth.login(data["username"], data["password"])
        status = 200 if success else 401
        return jsonify({"success": success, "message": message}), status

    return app


# Allow running with: python src/omnium/api.py
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)

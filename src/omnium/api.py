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
from src.omnium.algorithms.switcher import AlgorithmSwitcher, AVAILABLE_ALGORITHMS
from src.omnium.orchestration import orchestrator
from src.omnium.backtesting.backtest import run_backtest
from src.omnium.evaluation.compare import compare_algorithms


def create_app() -> Flask:
    """App factory — creates and configures the Flask application."""
    app = Flask(__name__)

    # Shared instances
    auth = RegistrationSystem()
    switcher = AlgorithmSwitcher()

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

    # ── Trading ──

    @app.post("/trading/tick")
    def trading_tick():
        data = request.get_json()
        if not data or "account_id" not in data or "asset_id" not in data:
            return jsonify({"error": "account_id and asset_id are required"}), 400
        result = orchestrator.tick(data["account_id"], data["asset_id"], switcher)
        return jsonify({
            "asset_id": result.asset_id,
            "symbol": result.symbol,
            "action": result.action,
            "price": result.price,
            "shares_held": result.shares_held,
            "trade_executed": result.trade_executed,
            "message": result.message,
        })

    @app.get("/trading/status/<int:account_id>/<int:asset_id>")
    def trading_status(account_id: int, asset_id: int):
        status = orchestrator.get_status(account_id, asset_id, switcher)
        return jsonify(status)

    @app.post("/trading/config")
    def trading_config():
        data = request.get_json()
        if not data:
            return jsonify({"error": "config parameters required"}), 400
        switcher.update_config(data)
        return jsonify(switcher.get_config())

    @app.get("/trading/config")
    def trading_config_get():
        return jsonify(switcher.get_config())

    @app.post("/trading/switch")
    def trading_switch():
        data = request.get_json()
        if not data or "algorithm" not in data:
            return jsonify({"error": "algorithm name required"}), 400
        name = data["algorithm"]
        if switcher.switch(name):
            return jsonify({"active": name})
        return jsonify({"error": f"unknown algorithm '{name}'", "available": AVAILABLE_ALGORITHMS}), 400

    # ── Backtesting ──

    @app.post("/backtest/run")
    def backtest_run():
        data = request.get_json()
        if not data or "asset_id" not in data:
            return jsonify({"error": "asset_id is required"}), 400
        result = run_backtest(
            asset_id=data["asset_id"],
            starting_cash=data.get("starting_cash", 100_000),
            limit=data.get("limit", 90),
            config=data.get("config"),
        )
        return jsonify({
            "asset_id": result.asset_id,
            "symbol": result.symbol,
            "algorithm": result.algorithm,
            "starting_cash": result.starting_cash,
            "ending_cash": result.ending_cash,
            "shares_held": result.shares_held,
            "total_value": result.total_value,
            "return_pct": result.return_pct,
            "total_trades": result.total_trades,
            "buys": result.buys,
            "sells": result.sells,
            "trade_log": result.trade_log,
        })

    # ── Evaluation ──

    @app.get("/evaluation/compare")
    def evaluation_compare():
        asset_id = request.args.get("asset_id", type=int)
        if not asset_id:
            return jsonify({"error": "asset_id query parameter required"}), 400
        limit = request.args.get("limit", 90, type=int)
        result = compare_algorithms(asset_id=asset_id, limit=limit)
        return jsonify(result)

    return app


# Allow running with: python src/omnium/api.py
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)

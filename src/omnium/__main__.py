"""omnium — Entry point for `python -m omnium`."""

from src.omnium.api import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)

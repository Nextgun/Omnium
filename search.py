import re

from database import get_all_assets, get_asset_by_symbol, get_latest_price


def search_securities(query):
    """
    Search for assets by company name or ticker symbol.

    Args:
        query: The text the user typed into the search bar.

    Returns:
        A list of matching assets, e.g. [{"id": 1, "symbol": "GOOGL", "name": "Google"}, ...]
        Returns an empty list if no results found or query is empty.
    """
    if not query or not query.strip():
        return []

    query = query.strip().lower()

    try:
        assets = get_all_assets()
    except Exception:
        return []

    results = []
    for asset in assets:
        if query in asset.get("symbol", "").lower() or query in asset.get("name", "").lower():
            results.append({
                "id": asset.get("id"),
                "symbol": asset.get("symbol"),
                "name": asset.get("name")
            })

    return results


def get_security_details(symbol):
    """
    Get detailed information about an asset by its exact ticker symbol.

    Args:
        symbol: A string containing the exact ticker symbol (e.g. "AAPL").

    Returns:
        A dictionary with asset info and latest price data, or None if not found.
    """
    if not symbol or not symbol.strip():
        return None

    symbol = symbol.strip().upper()

    # Validate ticker symbol format (1-5 letters only)
    if not re.match(r'^[A-Z]{1,5}$', symbol):
        return None

    try:
        asset = get_asset_by_symbol(symbol)
    except Exception:
        return None

    if not asset:
        return None

    try:
        latest_price = get_latest_price(asset.get("id"))
    except Exception:
        latest_price = None

    details = {
        "id": asset.get("id"),
        "symbol": asset.get("symbol"),
        "name": asset.get("name"),
        "latest_price": latest_price
    }

    return details

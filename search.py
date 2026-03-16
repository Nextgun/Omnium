"""
==========================
search.py - search function
author: Eli Ventura
date created: ??? check later on github.
date last modified: 3/16/2026
==========================

insert description here.

"""

import re # regular expression
from database.db import get_asset_by_symbol, get_latest_price, search_assets

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

    query = query.strip().upper()

    try:
        assets = search_assets(query)

    except Exception:
        print("no results found.")
        return []        

    results = []
    for asset in assets:
        if query in asset.get("symbol", "").upper() or query in asset.get("name", "").upper():
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

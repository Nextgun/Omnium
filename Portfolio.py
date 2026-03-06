from tabulate import tabulate
import logging
import json

#trade logging function
#code an entry/exit system maybe purches and such
#do something that for prices on portfolio
#logging of trades
logging.basicConfig(
    filename="trading.log", 
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Program started")
logging.warning("This is a warning")
logging.error("Something failed")


def log_trade(asset_id, side, quantity, price):
    logging.info(f"{asset_id} {quantity} {side} at ${price}")

log_trade("Company Example", "buy", 10, 185.50)


#portfolio tracking
class Portfolio:
    def __init__(account_id):#do i put self here???
        account_id.positions = {}  # {"Company Example": {"quantity": 10, "avg_price": 180}} 

    def buy(account_id, asset_id, quantity, price):
        if asset_id in account_id.positions:
            pos = account_id.positions[asset_id]
            total_cost = pos["quantity"] * pos["avg_price"]
            total_cost += quantity * price
            total_quantity = pos["quantity"] + quantity

            pos["quantity"] = total_quantity
            pos["avg_price"] = total_cost / total_quantity
        else:
                account_id.positions[asset_id] = {
                "quantity": quantity,
                "avg_price": price
            }

    def sell(account_id, asset_id, quantity):
        if asset_id in account_id.positions:
            account_id.positions[asset_id]["quantity"] -= quantity
            if account_id.positions[asset_id]["quantity"] <= 0:
                del account_id.positions[asset_id]

    def show(account_id):
        for account_id, data in account_id.positions.items():  #for asset_id, data in account_id.positions.items():
            print(account_id, data)

account_id = Portfolio()

account_id.buy(asset_id, 10, 180)
account_id.buy(asset_id, 5, 190)
account_id.sell(asset_id, 3)
account_id.show()

#extra code, it probably does something (maybe)
def buy(account_id, asset_id, quantity, price):
    logging.info(f"BUY {quantity} {asset_id} at {price}")
    ... #not completed
    
#not required
def portfolio_value(account_id, market_prices):
    total = 0
    for side, data in account_id.positions.items():
        total += data["quantity"] * market_prices[side]
    return total

prices = {"Company Example": 200}
print("Current portfolio value:", account_id.portfolio_value(prices))

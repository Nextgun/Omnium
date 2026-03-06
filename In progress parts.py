from tabulate import tabulate
import logging
import json


#extra code, it probably does something (maybe)
def buy(account_id, asset_id, quantity, price):
    logging.info(f"BUY {quantity} {asset_id} at {price}")
    ...

#some sort of filesaving

def save_portfolio(account_id):
    with open("account.json", "w") as f:
        json.dump(account_id.positions, f)

def load_portfolio():
    try:
        with open("account_id", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
#File not found shouldn't be needed^
#this is formatted like that old assignment, it's not supposed to be


#logging of trades
#this feels formatted like a database, can't remember if that's what it's supposed to be exactly
logging.basicConfig(
    filename="trading.log", 
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

#look more into loggign to cross-reference and make sure these are correct
logging.info() 
logging.warning()
logging.error()


#unfinished function, expand more on the logging
#might go back to that exit/entry idea
def log_trade(asset_id, side, quantity, price):
    logging.info(f"{asset_id} {quantity} {side} at ${price}")

log_trade("Company Example", "buy", 10, 185.50)



#Examples,, not sure if they work completly
#they didn't work initally, aka, didn;t print but they also weren't the part that bugged out
#either get some database data, or make my own with the current structure I have
account_id.buy("Company Example", 10, 180)
account_id.buy("Company Example", 5, 190)
account_id.sell("Company Example", 3)

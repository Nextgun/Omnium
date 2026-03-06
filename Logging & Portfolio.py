from tabulate import tabulate
import logging
import json

#trade logging function
#code an entry/exit system maybe for logging?
#do something that for prices on portfolio

#impliment a [run code] here 

#import from data base here probably
import database as pd
#whatis the database? that probably works? reference that 
import databse 
#insert the 


#portfolio tracking
#keep in mind the universal variables
class Portfolio:
    def __init__(account_id):#do i put self here, that's what a lot of things say???
        account_id.positions = {}  # {"Company Example": {"quantity": 10, "avg_price": 180}} 

#[pos] is a temporary variable
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
# check and see if the variables are right in both areas
    def sell(account_id, asset_id, quantity):
        if asset_id in account_id.positions:
            account_id.positions[asset_id]["quantity"] -= quantity
            if account_id.positions[asset_id]["quantity"] <= 0:
                del account_id.positions[asset_id]

    def show(account_id):
        for account_id, data in account_id.positions.items():  #for asset_id, data in account_id.positions.items():
            print(account_id, data)

account_id = Portfolio()
account_id.show()
# as of this line of code ^, it will run without errors
    


#i think there's supposed to be a push and pull here
#like, pull from the database for the data and then push the new formulated data into the database
#ask later


#insert table here when something is bought or sold


#portfolio review
#there's something wrong with the function, look into it more
def portfolio_value(account_id, market_prices, side):
    total = 0
    for side, data in account_id.positions.items():
        total += data["quantity"] * market_prices[side]
    return total

prices = {"Company Example": 200} #i do think asset_id should be here, it won't work yet though
print("Current portfolio value:", account_id.portfolio_value(prices))


#Todo stil:: 
# #set up 'read me' properly
##finish linking everything together
#EXAMPLES
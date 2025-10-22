import pandas as pd

class PNLCalculator:
    def __init__(self, upper_crossover=10000, lower_crossover=-10000):
        self.upper_crossover = upper_crossover
        self.lower_crossover = lower_crossover
        self.booked_pnl = 0.0

    def calculate_pnl(self, call_sell_price, call_buy_price, put_sell_price, put_buy_price, call_sell_qty, call_buy_qty, put_sell_qty, put_buy_qty):
        return (call_sell_price * call_sell_qty + put_sell_price * put_sell_qty) + (call_buy_price * call_buy_qty + put_buy_price * put_buy_qty)


    # Additional methods for qty adjustment and tracking can be added here

def compute_trade_pnl(entry_type, entry_price, exit_price, qty):
    """
    Compute PNL for a closed position.
    entry_type: 'buy' or 'sell'
    entry_price: price at entry
    exit_price: price at exit
    qty: positive integer
    """
    if entry_type == 'buy':
        return (exit_price - entry_price) * qty
    elif entry_type == 'sell':
        return (entry_price - exit_price) * qty
    else:
        raise ValueError('entry_type must be buy or sell')

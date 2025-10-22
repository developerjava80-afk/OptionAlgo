import pandas as pd
import numpy as np
from pnl_logic import compute_trade_pnl

def calculate_atr(high, low, close, period=14):
    high = pd.Series(high)
    low = pd.Series(low)
    close = pd.Series(close)
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()
    return atr

def manage_position_with_exit_stoploss(price_series, position_type, entry_price, contract_name, total_pnl=0.0):
    # price_series: pd.Series of option price
    # position_type: 'long' or 'short'
    # entry_price: float
    # contract_name: str
    # total_pnl: running total pnl
    period_atr = 14
    period_bb = 20
    std_bb = 2
    close = price_series.astype(float)
    # For ATR, use close as high/low for options (no OHLC)
    high = close
    low = close
    atr = calculate_atr(high, low, close, period=period_atr)
    ma20 = close.rolling(window=period_bb, min_periods=period_bb).mean()
    std20 = close.rolling(window=period_bb, min_periods=period_bb).std()
    upper_bb = ma20 + std_bb * std20
    lower_bb = ma20 - std_bb * std20
    mid_bb = ma20
    position_open = True
    exit_reason = None
    exit_price = None
    for idx in range(len(close)):
        if idx < max(period_atr, period_bb):
            continue
        price = close.iloc[idx]
        bb_high = upper_bb.iloc[idx]
        bb_low = lower_bb.iloc[idx]
        bb_mid = mid_bb.iloc[idx]
        # Long position exit logic
        if position_type == 'long' and position_open:
            if price > bb_high:
                exit_reason = 'Profit: Price crossed above upper BB'
                exit_price = price
                position_open = False
            elif price < bb_mid:
                exit_reason = 'Stop: Price crossed below middle BB'
                exit_price = price
                position_open = False
        # Short position exit logic
        elif position_type == 'short' and position_open:
            if price < bb_low:
                exit_reason = 'Profit: Price crossed below lower BB'
                exit_price = price
                position_open = False
            elif price > bb_mid:
                exit_reason = 'Stop: Price crossed above middle BB'
                exit_price = price
                position_open = False
        if not position_open:
            trade_pnl = compute_trade_pnl('buy' if position_type == 'long' else 'sell', entry_price, exit_price, 75)
            total_pnl += trade_pnl
            print(f"[{contract_name}] {position_type.upper()} EXIT at {exit_price:.2f} (entry {entry_price:.2f}) | {exit_reason} | Trade PNL={trade_pnl:.2f} | Total PNL={total_pnl:.2f}")
            break
    if position_open:
        print(f"[{contract_name}] {position_type.upper()} still open. Entry: {entry_price:.2f}")
    return total_pnl

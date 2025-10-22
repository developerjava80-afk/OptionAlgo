"""
Simple example: download historical data for an instrument and run a moving-average crossover backtest.
"""
import os
import sys
from kite_hist import KiteHistClient
import pandas as pd

API_KEY = os.getenv('KITE_API_KEY')
ACCESS_TOKEN = os.getenv('KITE_ACCESS_TOKEN')

def sma_cross_backtest(df, short=5, long=20):
    df = df.copy()
    df['sma_short'] = df['close'].rolling(short).mean()
    df['sma_long'] = df['close'].rolling(long).mean()
    df = df.dropna()
    position = 0
    entry_price = 0
    trades = []
    for idx, row in df.iterrows():
        if row['sma_short'] > row['sma_long'] and position == 0:
            position = 1
            entry_price = row['close']
        elif row['sma_short'] < row['sma_long'] and position == 1:
            position = 0
            trades.append(row['close'] - entry_price)
    return trades

def main():
    # Prompt for missing credentials interactively (access tokens change frequently)
    api_key = API_KEY
    access_token = ACCESS_TOKEN
    if not api_key:
        if sys.stdin is not None and sys.stdin.isatty():
            api_key = input('Enter Kite API key: ').strip()
        else:
            print('KITE_API_KEY not set and not running interactively')
            sys.exit(1)

    if not access_token:
        if sys.stdin is not None and sys.stdin.isatty():
            access_token = input('Enter Kite access token (request_token-generated access_token): ').strip()
        else:
            print('KITE_ACCESS_TOKEN not set and not running interactively')
            sys.exit(1)

    client = KiteHistClient(api_key, access_token)
    token = int(input('Enter instrument_token: ').strip())
    from_date = input('From date (YYYY-MM-DD): ').strip()
    to_date = input('To date (YYYY-MM-DD): ').strip()
    df = client.get_historical(token, from_date, to_date, interval='15minute')
    if df.empty:
        print('No data returned')
        
        return
    trades = sma_cross_backtest(df)
    print('Trades PnL:', trades)
    print('Total PnL:', sum(trades))


if __name__ == '__main__':
    main()

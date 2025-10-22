import pandas as pd
from manage_reports import save_row_details_report
from pnl_logic import compute_trade_pnl

def process_put_data(df, table_name, put_columns):
    results = []
    all_row_details = {}
    contract_name = ""
    option_cols = put_columns
    if not option_cols:
        raise ValueError('No put option contract columns provided')
    contract_pnl = []
    for contract in option_cols:
        contract_name = table_name+"_"+contract
        price = df[contract].astype(float)
        close = price
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14, min_periods=14).mean()
        avg_loss = loss.rolling(window=14, min_periods=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        position = None
        entry_price = None
        entry_type = None
        qty = 0
        total_pnl = 0.0
        closed_trades = []
        row_details = []
        profit_target = None
        trail_exit_price = None
        trail_high = None
        trail_low = None
        for idx in range(len(close)):
            if idx < 30:
                continue
            try:
                macd_prev = macd_line.iloc[idx - 1]
                sig_prev = signal_line.iloc[idx - 1]
                macd_curr = macd_line.iloc[idx]
                sig_curr = signal_line.iloc[idx]
                macd_hist_prev = macd_hist.iloc[idx - 1]
                macd_hist_curr = macd_hist.iloc[idx]
                rsi_curr = rsi.iloc[idx]
                price_curr = close.iloc[idx]
            except Exception:
                continue
            signal_text = None
            event_printed = False
            bull_signal = (macd_prev <= sig_prev) and (macd_curr > sig_curr) and (rsi_curr is not None and rsi_curr > 70)
            bear_signal = (macd_prev >= sig_prev) and (macd_curr < sig_curr) and (rsi_curr is not None and rsi_curr < 30)
            # Entry/exit logic
            if bull_signal:
                signal_text = 'Bullish Confirmed Signal'
                if position is None:
                    position = 'long'
                    entry_type = 'buy'
                    entry_price = price_curr
                    qty = 75
                    profit_target = entry_price * 1.1
                    print(f"[{contract}] LONG opened at {entry_price:.2f}, qty={qty}, profit_target={profit_target:.2f}, total PNL={total_pnl:.2f}")
            elif bear_signal:
                signal_text = 'Bearish Confirmed Signal'
                if position is None:
                    position = 'short'
                    entry_type = 'sell'
                    entry_price = price_curr
                    qty = 75
                    profit_target = entry_price * 0.9
                    print(f"[{contract}] SHORT opened at {entry_price:.2f}, qty={qty}, profit_target={profit_target:.2f}, total PNL={total_pnl:.2f}")
            # Trailing profit booking logic
            if position == 'long':
                if price_curr < entry_price:
                    diff = entry_price - price_curr
                    if entry_price * 1.1 - profit_target < diff:
                        profit_target = entry_price * 1.1 - diff
                if price_curr >= profit_target:
                    exit_price = price_curr
                    trade_pnl = compute_trade_pnl('buy', entry_price, exit_price, qty)
                    total_pnl += trade_pnl
                    print(f"[{contract}] LONG EXIT at {exit_price:.2f} (entry {entry_price:.2f}) | Trailing profit booked | Trade PNL={trade_pnl:.2f} | Total PNL={total_pnl:.2f}")
                    position = None
                    profit_target = None
                    entry_price = None
            elif position == 'short':
                if price_curr > entry_price:
                    diff = price_curr - entry_price
                    if profit_target - entry_price * 0.9 < diff:
                        profit_target = entry_price * 0.9 + diff
                if price_curr <= profit_target:
                    exit_price = price_curr
                    trade_pnl = compute_trade_pnl('sell', entry_price, exit_price, qty)
                    total_pnl += trade_pnl
                    print(f"[{contract}] SHORT EXIT at {exit_price:.2f} (entry {entry_price:.2f}) | Trailing profit booked | Trade PNL={trade_pnl:.2f} | Total PNL={total_pnl:.2f}")
                    position = None
                    profit_target = None
                    entry_price = None
            row_details.append({
                'contract': contract,
                'index': int(idx),
                'price': float(price_curr),
                'macd': float(macd_curr) if pd.notna(macd_curr) else None,
                'signal': float(sig_curr) if pd.notna(sig_curr) else None,
                'macd_hist': float(macd_hist_curr) if pd.notna(macd_hist_curr) else None,
                'rsi': float(rsi_curr) if pd.notna(rsi_curr) else None,
                'trade_signal': signal_text,
                'position': position,
                'entry_price': entry_price,
                'target_price': profit_target,
                'total_pnl': total_pnl,
            })
        from manage_reports import save_row_details_report
        save_row_details_report(row_details, contract_name)
        contract_pnl.append({'Contract': contract_name, 'PnL': total_pnl})
    return pd.DataFrame(contract_pnl)

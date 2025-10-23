import pandas as pd
from manage_reports import save_row_details_report
from pnl_logic import compute_trade_pnl

def process_option_data(df: pd.DataFrame, table_name: str, option_columns: list[str]) -> pd.DataFrame:
    """
    Generic processor for option contracts (both Calls and Puts).
    Applies MACD + RSI signals gated by EMA200 trend filter, supports reversal on opposite signal,
    0.5% trailing profit targets with dynamic adjustment, and forced exit if target crosses entry.

    Returns a DataFrame with columns: Contract, PnL
    """
    if not option_columns:
        raise ValueError('No option contract columns provided')

    contract_pnl = []

    for contract in option_columns:
        contract_name = f"{table_name}_{contract}"
        price = df[contract].astype(float)
        close = price

        # Indicators
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line
        ema200 = close.ewm(span=200, adjust=False).mean()

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14, min_periods=14).mean()
        avg_loss = loss.rolling(window=14, min_periods=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # State
        position = None  # 'long' | 'short' | None
        entry_price = None
        qty = 0
        total_pnl = 0.0
        closed_trades = []
        row_details = []
        profit_target = None

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
                ema200_curr = ema200.iloc[idx]
            except Exception:
                continue

            signal_text = None

            bull_signal = (
                (macd_prev <= sig_prev)
                and (macd_curr > sig_curr)
                and (rsi_curr is not None and rsi_curr > 70)
                and (pd.notna(ema200_curr) and price_curr > ema200_curr)
            )
            bear_signal = (
                (macd_prev >= sig_prev)
                and (macd_curr < sig_curr)
                and (rsi_curr is not None and rsi_curr < 30)
                and (pd.notna(ema200_curr) and price_curr < ema200_curr)
            )

            # Entries and reversals
            if bull_signal:
                signal_text = 'Bullish Confirmed Signal'
                if position is None:
                    position = 'long'
                    entry_price = price_curr
                    qty = 75 if qty == 0 else qty
                    profit_target = entry_price * 1.005  # 0.5%
                    print(f"[{contract}] LONG opened at {entry_price:.2f}, qty={qty}, profit_target={profit_target:.2f}, total PNL={total_pnl:.2f}")
                elif position == 'short':
                    # Reverse SHORT -> LONG
                    exit_price = price_curr
                    trade_pnl = compute_trade_pnl('sell', entry_price, exit_price, qty)
                    total_pnl += trade_pnl
                    closed_trades.append({
                        'side': 'short', 'entry': float(entry_price), 'exit': float(exit_price),
                        'qty': qty, 'pnl': float(trade_pnl), 'reason': 'Reversal on bull signal', 'index': int(idx)
                    })
                    print(f"[{contract}] SHORT EXIT (reversal) at {exit_price:.2f} (entry {entry_price:.2f}) | PNL={trade_pnl:.2f} | Total PNL={total_pnl:.2f}")
                    position = 'long'
                    entry_price = price_curr
                    qty = 75 if qty == 0 else qty
                    profit_target = entry_price * 1.005
                    signal_text += ' (Reversal)'
                    print(f"[{contract}] LONG opened (reversal) at {entry_price:.2f}, qty={qty}, profit_target={profit_target:.2f}, total PNL={total_pnl:.2f}")
            elif bear_signal:
                signal_text = 'Bearish Confirmed Signal'
                if position is None:
                    position = 'short'
                    entry_price = price_curr
                    qty = 75 if qty == 0 else qty
                    profit_target = entry_price * 0.995  # 0.5%
                    print(f"[{contract}] SHORT opened at {entry_price:.2f}, qty={qty}, profit_target={profit_target:.2f}, total PNL={total_pnl:.2f}")
                elif position == 'long':
                    # Reverse LONG -> SHORT
                    exit_price = price_curr
                    trade_pnl = compute_trade_pnl('buy', entry_price, exit_price, qty)
                    total_pnl += trade_pnl
                    closed_trades.append({
                        'side': 'long', 'entry': float(entry_price), 'exit': float(exit_price),
                        'qty': qty, 'pnl': float(trade_pnl), 'reason': 'Reversal on bear signal', 'index': int(idx)
                    })
                    print(f"[{contract}] LONG EXIT (reversal) at {exit_price:.2f} (entry {entry_price:.2f}) | PNL={trade_pnl:.2f} | Total PNL={total_pnl:.2f}")
                    position = 'short'
                    entry_price = price_curr
                    qty = 75 if qty == 0 else qty
                    profit_target = entry_price * 0.995
                    signal_text += ' (Reversal)'
                    print(f"[{contract}] SHORT opened (reversal) at {entry_price:.2f}, qty={qty}, profit_target={profit_target:.2f}, total PNL={total_pnl:.2f}")

            # Trailing profit logic and forced exit when target crosses entry
            if position == 'long' and entry_price is not None:
                if price_curr < entry_price:
                    diff = entry_price - price_curr
                    if (entry_price * 1.005 - profit_target) < diff:
                        profit_target = entry_price * 1.005 - diff
                if profit_target is not None and profit_target <= entry_price:
                    exit_price = price_curr
                    trade_pnl = compute_trade_pnl('buy', entry_price, exit_price, qty)
                    total_pnl += trade_pnl
                    print(f"[{contract}] LONG EXIT at {exit_price:.2f} (entry {entry_price:.2f}) | Target <= entry (forced) | Trade PNL={trade_pnl:.2f} | Total PNL={total_pnl:.2f}")
                    position = None
                    profit_target = None
                    entry_price = None
                elif profit_target is not None and price_curr >= profit_target:
                    exit_price = price_curr
                    trade_pnl = compute_trade_pnl('buy', entry_price, exit_price, qty)
                    total_pnl += trade_pnl
                    print(f"[{contract}] LONG EXIT at {exit_price:.2f} (entry {entry_price:.2f}) | Trailing profit booked | Trade PNL={trade_pnl:.2f} | Total PNL={total_pnl:.2f}")
                    position = None
                    profit_target = None
                    entry_price = None
            elif position == 'short' and entry_price is not None:
                if price_curr > entry_price:
                    diff = price_curr - entry_price
                    if (profit_target - entry_price * 0.995) < diff:
                        profit_target = entry_price * 0.995 + diff
                if profit_target is not None and profit_target >= entry_price:
                    exit_price = price_curr
                    trade_pnl = compute_trade_pnl('sell', entry_price, exit_price, qty)
                    total_pnl += trade_pnl
                    print(f"[{contract}] SHORT EXIT at {exit_price:.2f} (entry {entry_price:.2f}) | Target >= entry (forced) | Trade PNL={trade_pnl:.2f} | Total PNL={total_pnl:.2f}")
                    position = None
                    profit_target = None
                    entry_price = None
                elif profit_target is not None and price_curr <= profit_target:
                    exit_price = price_curr
                    trade_pnl = compute_trade_pnl('sell', entry_price, exit_price, qty)
                    total_pnl += trade_pnl
                    print(f"[{contract}] SHORT EXIT at {exit_price:.2f} (entry {entry_price:.2f}) | Trailing profit booked | Trade PNL={trade_pnl:.2f} | Total PNL={total_pnl:.2f}")
                    position = None
                    profit_target = None
                    entry_price = None

            # Row details for analysis/export
            row_details.append({
                'contract': contract,
                'index': int(idx),
                'price': float(price_curr),
                'ema200': float(ema200_curr) if pd.notna(ema200_curr) else None,
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

        # Save per-contract details and summary
        save_row_details_report(row_details, contract_name)
        contract_pnl.append({'Contract': contract_name, 'PnL': total_pnl})

    return pd.DataFrame(contract_pnl)

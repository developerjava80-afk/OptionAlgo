from db_connector import DBConnector
from process_option_data import process_option_data
from manage_reports import save_results_to_excel
import pandas as pd
import os
import datetime
import re

class OptionAlgoMain:
    def __init__(self, config):
        self.config = config
        self.db = DBConnector(config)
        

    def select_option_columns(self, df, base_price):
        columns = df.columns.tolist()
        # Find all call and put strikes
        call_strikes = sorted([int(col[1:]) for col in columns if re.match(r'^C\d+$', col)])
        put_strikes = sorted([int(col[1:]) for col in columns if re.match(r'^P\d+$', col)])
        # Find the call just above base_price
        c_col = None
        for strike in call_strikes:
            if strike > base_price:
                c_col = f'C{strike}'
                break
        # Find the put just below base_price
        p_col = None
        for strike in reversed(put_strikes):
            if strike < base_price:
                p_col = f'P{strike}'
                break
        c_cols = [c_col] if c_col else []
        p_cols = [p_col] if p_col else []
        print(f"Selected OTM call column: {c_cols}")
        print(f"Selected OTM put column: {p_cols}")
        return c_cols, p_cols

    def run(self):
        dfs, table_names = self.db.get_tables()
        all_contracts = []
        no_of_table = 100
        for i in range(min(no_of_table, len(dfs))):
            df = dfs[i]
            table_name_clean = table_names[i].strip()[:20] if isinstance(table_names[i], str) else table_names[i]
            print(f"\nProcessing table: {table_name_clean}")
            call_df = pd.DataFrame()
            put_df = pd.DataFrame()
            # Retrieve BankNifty price from 30th row (index 29)
            # Try common column names for BankNifty spot/underlying
            banknifty_col = None
            for cand in ['BANKNIFTY', 'banknifty', 'underlying', 'spot', 'base_price', 'underlying_price']:
                if cand in df.columns:
                    banknifty_col = cand
                    break
            if banknifty_col is None:
                # fallback: first numeric non-option column
                numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and not c.startswith(('C','P'))]
                if numeric_cols:
                    banknifty_col = numeric_cols[0]
            if banknifty_col is None:
                print("No BankNifty/underlying column found, skipping table.")
                continue
            if len(df) < 30:
                print("Not enough rows to get 30th row price, skipping table.")
                continue
            banknifty_price = float(df[banknifty_col].iloc[29])
            c_cols, p_cols = self.select_option_columns(df, banknifty_price)
            opt_cols = c_cols + p_cols
            # Process only the selected OTM columns using unified processor
            combined_df = pd.DataFrame()
            if opt_cols:
                combined_df = process_option_data(df, table_name_clean, opt_cols)
            all_contracts.append(combined_df)
        if all_contracts:
            final_df = pd.concat(all_contracts, ignore_index=True)
            save_results_to_excel(final_df[['Contract', 'PnL']])
        else:
            print("No contracts processed.")

if __name__ == "__main__":
    config = {
        'user': 'root',
        'password': 'hindus',
        'host': 'localhost',
        'database': 'market_data',
    }
    app = OptionAlgoMain(config)
    app.run()

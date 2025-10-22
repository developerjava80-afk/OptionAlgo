import os
import sys
from typing import Optional, TYPE_CHECKING
import pandas as pd

if TYPE_CHECKING:
    # for type checking only
    from kiteconnect import KiteConnect

try:
    from kiteconnect import KiteConnect
except Exception:
    KiteConnect = None


class KiteHistClient:
    def __init__(self, api_key: str, access_token: str, kite=None):
        self.api_key = api_key
        # If access_token is falsy, prompt the user on the terminal (interactive only)
        if not access_token:
            if sys.stdin is not None and sys.stdin.isatty():
                try:
                    access_token = input('Enter Kite access token (request_token-generated access_token): ').strip()
                except Exception:
                    access_token = None
            else:
                raise RuntimeError('No access token provided and not running interactively. Pass access_token param.')

        self.access_token = access_token
        if kite is not None:
            self.kite = kite
        else:
            if KiteConnect is None:
                raise ImportError('kiteconnect package not installed. See requirements.txt')
            self.kite = KiteConnect(api_key=api_key)
            self.kite.set_access_token(access_token)

    def get_historical(self, instrument_token: int, from_date: str, to_date: str, interval: str = '15minute') -> pd.DataFrame:
        """Download historical data for the instrument token.

        from_date/to_date: ISO strings 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD'
        interval: 'minute', '15minute', 'day', etc. See Kite API for supported intervals.
        """
        data = self.kite.historical_data(instrument_token, from_date, to_date, interval)
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        # ensure timestamp is datetime
        df['date'] = pd.to_datetime(df['date'])
        return df

    def get_fno_instruments(self, exchange: str = 'NFO') -> pd.DataFrame:
        """Return all instruments that belong to the F&O segment (NFO) as a DataFrame.

        This method attempts to fetch instruments via KiteConnect.instruments(). If kiteconnect
        isn't available or the call fails, it falls back to reading a local CSV named
        'instruments_NSE.csv' at the repository root.

        The returned DataFrame will include at least these columns if available:
        ['instrument_token', 'exchange', 'tradingsymbol', 'name', 'segment', 'expiry']
        """
        # Try to get from kite if possible
        instruments = None
        if hasattr(self, 'kite') and self.kite is not None:
            try:
                instruments = self.kite.instruments()
            except Exception:
                instruments = None

        if instruments:
            df = pd.DataFrame(instruments)
        else:
            # fallback: try reading instruments_NSE.csv from repo root
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            csv_path = os.path.join(repo_root, 'instrumentsFNO_NSE.csv')
            if not os.path.exists(csv_path):
                # nothing we can do
                return pd.DataFrame()
            df = pd.read_csv(csv_path)

        # Normalize column names access patterns
        # Some instrument lists include 'segment' or 'instrument_type'; attempt to detect FNO
        cols = df.columns.str.lower()
        # prefer 'segment' column if present
        segment_col = None
        for c in df.columns:
            if c.lower() in ('segment', 'instrument_type'):
                segment_col = c
                break

        exchange_col = None
        for c in df.columns:
            if c.lower() == 'exchange':
                exchange_col = c
                break

        if segment_col is not None:
            fno_df = df[df[segment_col].str.upper().str.contains('FUT|OPT|FNO|F&O', na=False)]
        elif exchange_col is not None:
            fno_df = df[df[exchange_col].str.upper() == exchange.upper()]
        else:
            # best-effort: look for tradingsymbol suffixes like 'FUT' or 'EQ'
            ts_cols = [c for c in df.columns if c.lower() in ('tradingsymbol', 'symbol')]
            if not ts_cols:
                return pd.DataFrame()
            ts = ts_cols[0]
            fno_df = df[df[ts].str.contains('FUT|OPT', na=False)]

        # Ensure instrument_token is numeric where possible
        if 'instrument_token' in fno_df.columns:
            try:
                fno_df['instrument_token'] = fno_df['instrument_token'].astype(int)
            except Exception:
                pass

        return fno_df.reset_index(drop=True)

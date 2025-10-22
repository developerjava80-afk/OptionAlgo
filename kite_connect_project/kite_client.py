import json
import logging
import os
import time
from typing import Callable, Dict, Optional

from kiteconnect import KiteConnect, KiteTicker

# Basic wrapper for Kite Connect. This module stores the access token in a local file
# and exposes convenience functions to place/modify/cancel orders and subscribe to 
# tick-by-tick data for a given instrument token.

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

TOKEN_STORE = os.path.expanduser('~/.kite_token.json')


class KiteClient:
    def __init__(self, api_key: str, api_secret: str, token_store: str = TOKEN_STORE):
        self.api_key = api_key
        self.api_secret = api_secret
        self.token_store = token_store
        self.kite: Optional[KiteConnect] = None
        self.ticker: Optional[KiteTicker] = None
        self.access_token: Optional[str] = None

    def init_session(self, request_token: Optional[str] = None) -> str:
        """
        Initialize KiteConnect session. If request_token provided, exchanges it for access token
        and persists the token to disk. If token already exists on disk, uses that token.

        Returns the access token.
        """
        # If token file exists, try to load it. If JSON is corrupt, back it up and continue
        if os.path.exists(self.token_store) and request_token is None:
            try:
                with open(self.token_store, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get('access_token')
            except json.JSONDecodeError:
                # Rename the corrupt file and continue as if no token exists
                ts = int(time.time())
                corrupt_name = f"{self.token_store}.corrupt.{ts}"
                try:
                    os.rename(self.token_store, corrupt_name)
                    logger.warning('Token file %s was corrupt; renamed to %s', self.token_store, corrupt_name)
                except Exception:
                    logger.exception('Failed to rename corrupt token file %s', self.token_store)
                self.access_token = None

        self.kite = KiteConnect(api_key=self.api_key)

        if request_token:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data['access_token']
            # persist
            with open(self.token_store, 'w') as f:
                # Session `data` may contain datetime objects; ensure they're serializable
                json.dump(data, f, default=str)
            logger.info('Access token saved to %s', self.token_store)

        if self.access_token:
            self.kite.set_access_token(self.access_token)
            logger.info('Kite client initialized with access token')
            return self.access_token

        raise RuntimeError('No access token available. Provide request_token to init_session.')

    def start_ticker(self, on_tick: Callable[[Dict], None], instruments: list, threaded: bool = False):
        """
        Start KiteTicker websocket and subscribe to instruments (list of instrument tokens).
        on_tick is called with the tick dict.
        If threaded=True, the ticker runs in a background thread.
        """
        if not self.kite:
            raise RuntimeError('Kite client not initialized. Call init_session first.')

        api_key = self.api_key
        access_token = self.access_token
        if not access_token:
            raise RuntimeError('Access token not set. Call init_session.')

        self.ticker = KiteTicker(api_key, access_token)

        def _on_ticks(ws, ticks):
            for t in ticks:
                try:
                    on_tick(t)
                except Exception:
                    logger.exception('Error in on_tick')

        def _on_connect(ws, response):
            logger.info('Ticker connected, subscribing to %s', instruments)
            ws.subscribe(instruments)
            ws.set_mode(ws.MODE_FULL, instruments)

        def _on_close(ws, code, reason):
            logger.info('Ticker closed: %s %s', code, reason)

        def _on_error(ws, code, reason):
            logger.error('Ticker error: %s %s', code, reason)

        self.ticker.on_ticks = _on_ticks
        self.ticker.on_connect = _on_connect
        self.ticker.on_close = _on_close
        self.ticker.on_error = _on_error

        # run the ticker
        try:
            self.ticker.connect(threaded=threaded)
        except Exception:
            logger.exception('Failed to start ticker')

    # Order convenience wrappers
    def place_order(self, tradingsymbol: str, exchange: str, transaction_type: str, quantity: int, price: Optional[float] = None, order_type: str = 'MARKET', product: str = 'MIS') -> Dict:
        """
        Place an order. Returns Kite order response.
        transaction_type: 'BUY' or 'SELL'
        order_type: MARKET or LIMIT
        product: MIS, NRML etc.
        """
        if not self.kite:
            raise RuntimeError('Kite client not initialized. Call init_session first.')

        params = {
            'tradingsymbol': tradingsymbol,
            'exchange': exchange,
            'transaction_type': transaction_type,
            'quantity': quantity,
            'order_type': order_type,
            'product': product,
        }
        if price is not None and order_type == 'LIMIT':
            params['price'] = price

        logger.info('Placing order: %s', params)
        resp = self.kite.place_order(**params)
        return resp

    def modify_order(self, order_id: int, quantity: Optional[int] = None, price: Optional[float] = None) -> Dict:
        if not self.kite:
            raise RuntimeError('Kite client not initialized. Call init_session first.')
        params = {'order_id': order_id}
        if quantity is not None:
            params['quantity'] = quantity
        if price is not None:
            params['price'] = price
        logger.info('Modifying order: %s', params)
        return self.kite.modify_order(**params)

    def cancel_order(self, order_id: int) -> Dict:
        if not self.kite:
            raise RuntimeError('Kite client not initialized. Call init_session first.')
        logger.info('Cancelling order: %s', order_id)
        return self.kite.cancel_order(order_id=order_id)

    def get_instruments_df(self):
        # Downloads the instruments list (cached by kiteconnect) and returns a DataFrame
        if not self.kite:
            raise RuntimeError('Kite client not initialized. Call init_session first.')
        instruments = self.kite.instruments()
        import pandas as pd
        return pd.DataFrame(instruments)

    def save_instruments_csv(self, exchange: str = 'NSE', path: Optional[str] = None) -> str:
        """Download instruments list and save only rows for given exchange to CSV.

        Returns the path to the saved CSV file.
        """
        df = self.get_instruments_df()
        df_filtered = df[df['exchange'] == exchange].copy()
        if df_filtered.empty:
            raise RuntimeError(f'No instruments found for exchange {exchange}')
        if path is None:
            path = os.path.join(os.getcwd(), f'instruments_{exchange}.csv')
        df_filtered.to_csv(path, index=False)
        logger.info('Saved %d instruments for %s to %s', len(df_filtered), exchange, path)
        return path

    def find_instrument_token(self, exchange: str, tradingsymbol: str) -> Optional[int]:
        df = self.get_instruments_df()
        row = df[(df['exchange'] == exchange) & (df['tradingsymbol'] == tradingsymbol)]
        if row.empty:
            return None
        return int(row.iloc[0]['instrument_token'])

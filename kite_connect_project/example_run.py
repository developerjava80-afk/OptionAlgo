"""Example runner for kite_connect_project

Demonstrates: init_session (manual step to paste request_token), find_instrument_token and start_ticker
"""
from kite_client import KiteClient

API_KEY = 'egmcnayk2z9xsf2u'
API_SECRET = 'p771ous3zyhwn4lrpkbzm8uipcax2lnu'


def on_tick(tick):
    # tick is a dict with live fields from Kite Ticker
    print('TICK:', tick)


if __name__ == '__main__':
    kc = KiteClient(api_key=API_KEY, api_secret=API_SECRET)

    # If you already have token saved, this will load it.
    try:
        kc.init_session()
    except RuntimeError:
        print('No token found. Generate request token by visiting the kite login URL:')
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=API_KEY)
        print(kite.login_url())
        rt = input('Paste request_token from redirect URL (request_token=...): ').strip()
        kc.init_session(request_token=rt)

    # After login, download NSE instruments list to CSV for later offline lookup
    try:
        csv_path = kc.save_instruments_csv(exchange='NSE')
        print('Instruments saved to', csv_path)
    except Exception as e:
        print('Failed to save instruments CSV:', e)

    # Example: find BANKNIFTY weekly option symbol (replace with accurate tradingsymbol)
    # Example tradingsymbol: 'NIFTY21NOV17500CE' - adjust accordingly
    tradingsymbol = input('Enter tradingsymbol to subscribe (e.g. NIFTY21NOV17500CE): ').strip()
    token = kc.find_instrument_token('NSE', tradingsymbol)
    if not token:
        print('Instrument not found for', tradingsymbol)
    else:
        print('Found token', token)
        kc.start_ticker(on_tick, [token], threaded=False)

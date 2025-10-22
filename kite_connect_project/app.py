from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
import traceback
import importlib.util
import pathlib

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Don't import kite modules at import-time; load them lazily to avoid errors when packages
# aren't installed in the environment used for editing.
KiteHistClient = None

def _load_kite_hist():
    """Attempt to load KiteHistClient from kite-testing/kite_hist.py dynamically.
    Returns the class or None.
    """
    global KiteHistClient
    if KiteHistClient is not None:
        return KiteHistClient
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    hist_path = repo_root / 'kite-testing' / 'kite_hist.py'
    if not hist_path.exists():
        return None
    spec = importlib.util.spec_from_file_location('kite_testing.kite_hist', str(hist_path))
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        KiteHistClient = getattr(module, 'KiteHistClient', None)
    except Exception:
        traceback.print_exc()
        KiteHistClient = None
    return KiteHistClient


STRATEGIES = [
    {"id": "sma_cross", "name": "SMA Crossover"},
    {"id": "stub", "name": "Stub Strategy"},
]


def get_kc():
    """Return a KiteClient instance if available, else None."""
    # Lazy import to avoid import errors at module load
    try:
        from kite_client import KiteClient as _KiteClient
    except Exception:
        return None
    api_key = os.getenv('KITE_API_KEY')
    api_secret = os.getenv('KITE_API_SECRET')
    # Try to use token file if present; KiteClient will handle init
    try:
        # KiteClient constructor expects (api_key, api_secret, ...)
        return _KiteClient(api_key, api_secret)
    except Exception:
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/strategies')
def strategies():
    return jsonify(STRATEGIES)


@app.route('/api/symbols')
def symbols():
    q = request.args.get('q', '').strip().upper()
    try:
        kc = get_kc()
        if kc is None:
            # fallback: load a local instruments CSV if present
            import pandas as pd
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'instruments_NSE.csv')
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
            else:
                return jsonify({'error': 'Kite client not available and instruments CSV missing'}), 500
        else:
            df = kc.get_instruments_df()
        # filter by symbol or tradingsymbol
        df['search_key'] = df.get('tradingsymbol', df.get('symbol', '')).astype(str)
        if q:
            df = df[df['search_key'].str.contains(q, case=False, na=False)]
        # return list of objects {symbol, instrument_token, name}
        out = []
        for _, r in df.head(200).iterrows():
            out.append({
                'symbol': r.get('tradingsymbol') or r.get('symbol'),
                'instrument_token': int(r.get('instrument_token')) if r.get('instrument_token') else None,
                'name': r.get('name') if 'name' in r else r.get('tradingsymbol') or r.get('symbol')
            })
        return jsonify(out)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/run', methods=['POST'])
def run_strategy():
    data = request.json or {}
    symbol = data.get('symbol')
    instrument_token = data.get('instrument_token')
    strategy = data.get('strategy')
    params = data.get('params', {})

    if strategy == 'stub':
        return jsonify({'status': 'ok', 'result': f'stub executed for {symbol}'})

    if strategy == 'sma_cross':
        # run a quick historical SMA fetch if possible
        try:
            api_key = os.getenv('KITE_API_KEY')
            access_token = os.getenv('KITE_ACCESS_TOKEN')
            if KiteHistClient is None:
                return jsonify({'error': 'KiteHistClient not available on server'}), 500
            client = KiteHistClient(api_key, access_token)
            # default params
            from_date = params.get('from_date') or '2023-01-01'
            to_date = params.get('to_date') or '2023-12-31'
            interval = params.get('interval') or '15minute'
            df = client.get_historical(int(instrument_token), from_date, to_date, interval=interval)
            if df.empty:
                return jsonify({'error': 'no data returned for instrument'}), 500
            # compute a tiny SMA crossover report
            short = int(params.get('short', 5))
            long = int(params.get('long', 20))
            df['sma_short'] = df['close'].rolling(short).mean()
            df['sma_long'] = df['close'].rolling(long).mean()
            df = df.dropna()
            # simple backtest: count crossovers
            df['signal'] = (df['sma_short'] > df['sma_long']).astype(int)
            df['signal_shift'] = df['signal'].shift(1).fillna(0).astype(int)
            entries = int(((df['signal'] > df['signal_shift']) & (df['signal'] == 1)).sum())
            exits = int(((df['signal'] < df['signal_shift']) & (df['signal'] == 0)).sum())
            return jsonify({'status': 'ok', 'entries': entries, 'exits': exits, 'rows': len(df)})
        except Exception as e:
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'unknown strategy'}), 400


if __name__ == '__main__':
    # development server
    app.run(host='0.0.0.0', port=5000, debug=True)

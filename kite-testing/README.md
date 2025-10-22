# kite-testing

Small project to fetch historical data from Kite Connect and run simple strategy tests.

Usage
- Install requirements in your Python environment:

```powershell
pip install -r kite-testing\requirements.txt
```

- Provide your Kite API key and access token (environment variables or pass to the client).
- Run the example backtest:

```powershell
python kite-testing\example_backtest.py
```

Files
- `kite_hist.py` - lightweight wrapper to download historical OHLC data as a pandas DataFrame.
- `example_backtest.py` - example backtest using a simple moving-average crossover strategy.

Notes
- This project expects an active Kite Connect session (access token). Use the `kite_connect_project` helper or follow the Kite Connect login flow to obtain an access token.

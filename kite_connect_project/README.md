Kite Connect standalone project

This folder contains a small standalone Kite Connect helper project.

Files:
- kite_client.py      : Kite client wrapper (session, ticker, order helpers)
- requirements.txt    : dependencies
- example_run.py      : example usage to find NIFTY weekly option and subscribe to ticks

Quick start
1) Create a virtualenv and install dependencies:
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt

2) Register a Kite app and get API_KEY and API_SECRET.
3) Use `example_run.py` to initialise session and subscribe to tick data.

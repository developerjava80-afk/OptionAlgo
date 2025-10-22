# validate_kite_token.py
from kiteconnect import KiteConnect
import traceback

API_KEY = "egmcnayk2z9xsf2u"
ACCESS_TOKEN = "938BgW1OIHXyT4OewGgOLcatIczmWvXn"

k = KiteConnect(api_key=API_KEY)
try:
    k.set_access_token(ACCESS_TOKEN.strip())
    profile = k.profile()   # small call to check auth
    print("Token valid. Profile summary keys:", list(profile.keys()))
    print("User display name:", profile.get('user_name') or profile.get('user', {}).get('name'))
except Exception as e:
    print("Token validation failed:", type(e).__name__, str(e))
    traceback.print_exc()
"""Minimal quickstart. Run: MEXC_TOKEN=... python examples/quickstart.py"""

import os

from mexc_web import MexcClient
from mexc_web.rest.orders import ISOLATED, LIMIT, OPEN_LONG

client = MexcClient(os.environ.get("MEXC_TOKEN"))

# --- public (no token needed) ---
print("BTC ticker:", client.market.ticker("BTC_USDT")["data"]["lastPrice"])

if not client.token:
    raise SystemExit("set MEXC_TOKEN to try the private calls")

# --- balances ---
for a in client.account.assets()["data"]:
    if a["equity"]:
        print(f"{a['currency']}: equity={a['equity']} avail={a['availableBalance']}")

# --- place, modify, cancel a limit order ---
resp = client.orders.create(
    "BTC_USDT", side=OPEN_LONG, vol=1, type=LIMIT,
    price=30000, open_type=ISOLATED, leverage=20,
)
oid = resp["data"]["orderId"]
print("placed", oid)
print("open orders:", client.orders.open_orders("BTC_USDT"))
client.orders.cancel([oid])
print("cancelled")

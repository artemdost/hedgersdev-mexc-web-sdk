"""Stream trades + private order/position pushes.

Run: MEXC_TOKEN=... python examples/websocket_stream.py
Needs the ws extra:  pip install "mexc-web[ws]"
"""

import os
import time

from mexc_web import MexcWSClient


def on_msg(m):
    ch = m.get("channel", "")
    if ch == "push.deal":
        for d in m.get("data", []):
            side = "BUY" if d.get("T") == 1 else "SELL"
            print(f"{m.get('symbol')} {side} {d.get('p')} x {d.get('v')}")
    elif ch.startswith("push.personal"):
        print("PRIVATE", ch, m.get("data"))


ws = MexcWSClient(on_message=on_msg, token=os.environ.get("MEXC_TOKEN"))
ws.connect()
ws.sub_deal("BTC_USDT")
ws.personal_filter(["order", "position"])

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ws.close()

"""mexc-web — unofficial MEXC SDK using the browser (web) token.

MexcClient (web token) covers the *futures* web API — trading, positions,
plan/TP-SL/trailing orders, account, identity and market data. The web token
cannot move funds between wallets, so internal transfers (SPOT <-> FUTURES),
spot balances and deposit addresses live on MexcSpotClient, which uses an API
key (HMAC) — a separate credential.

Quick start::

    from mexc_web import MexcClient, MexcSpotClient

    client = MexcClient("YOUR_U_ID_TOKEN")
    print(client.account.assets())

    spot = MexcSpotClient("API_KEY", "API_SECRET")
    spot.transfer_to_futures(25, "USDT")
"""

from ._internal.errors import (
    MexcAPIError,
    MexcAuthError,
    MexcError,
    MexcHTTPError,
)
from .rest import MexcClient, MexcSpotClient
from .ws import MexcWSClient

__version__ = "0.1.0"

__all__ = [
    "MexcClient",
    "MexcSpotClient",
    "MexcWSClient",
    "MexcError",
    "MexcAuthError",
    "MexcHTTPError",
    "MexcAPIError",
    "__version__",
]

"""mexc-web — unofficial MEXC SDK using the browser (web) token.

MexcClient (web token) covers the *futures* web API — trading, positions,
plan/TP-SL/trailing orders, account, identity, market data and internal
transfers between wallets (spot / futures / funding, via client.wallet).
MexcSpotClient is an optional API-key (HMAC) alternative that also exposes
spot balances, transfers and deposit addresses.

Quick start::

    from mexc_web import MexcClient, MexcSpotClient

    client = MexcClient("YOUR_U_ID_TOKEN")
    print(client.account.assets())
    client.wallet.spot_to_funding(5, "USDT")   # move funds with the web token

    spot = MexcSpotClient("API_KEY", "API_SECRET")   # API-key alternative
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

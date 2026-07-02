"""mexc-web — unofficial MEXC SDK using the browser (web) token.

Spot is not covered here; MEXC's web token authorizes the *futures* web API
(trading, positions, plan/TP-SL/trailing orders, account & market data). The
web token cannot withdraw or transfer funds — those require the spot OpenAPI
(API key), which is intentionally out of scope.

Quick start::

    from mexc_web import MexcClient

    client = MexcClient("YOUR_U_ID_TOKEN")
    print(client.account.assets())
"""

from ._internal.errors import (
    MexcAPIError,
    MexcAuthError,
    MexcError,
    MexcHTTPError,
)
from .rest import MexcClient
from .ws import MexcWSClient

__version__ = "0.1.0"

__all__ = [
    "MexcClient",
    "MexcWSClient",
    "MexcError",
    "MexcAuthError",
    "MexcHTTPError",
    "MexcAPIError",
    "__version__",
]

"""REST clients for the MEXC futures web API and spot OpenAPI."""

from .client import MexcClient
from .spot import MexcSpotClient

__all__ = ["MexcClient", "MexcSpotClient"]

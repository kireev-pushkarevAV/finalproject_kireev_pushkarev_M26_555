import time
from abc import ABC, abstractmethod
from typing import Any

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    def __init__(self, config: ParserConfig) -> None:
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> dict[str, dict[str, Any]]:
        pass


class CoinGeckoClient(BaseApiClient):
    def fetch_rates(self) -> dict[str, dict[str, Any]]:
        ids = ",".join(self.config.CRYPTO_ID_MAP.values())
        params = {"ids": ids, "vs_currencies": self.config.BASE_CURRENCY.lower()}

        start_time = time.time()
        try:
            resp = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            raise ApiRequestError(f"Network error CoinGecko: {exc}") from exc

        id_to_crypto = {v: k for k, v in self.config.CRYPTO_ID_MAP.items()}
        result: dict[str, dict[str, Any]] = {}
        for coin_id, prices in data.items():
            code = id_to_crypto.get(coin_id)
            base_key = self.config.BASE_CURRENCY.lower()
            if code and base_key in prices:
                pair_key = f"{code}_{self.config.BASE_CURRENCY}"
                result[pair_key] = {
                    "rate": float(prices[base_key]),
                    "source": "CoinGecko",
                    "raw_id": coin_id,
                    "request_ms": elapsed_ms,
                    "status_code": resp.status_code,
                }
        return result


class ExchangeRateApiClient(BaseApiClient):
    def fetch_rates(self) -> dict[str, dict[str, Any]]:
        key = self.config.EXCHANGERATE_API_KEY
        if not key:
            raise ApiRequestError(
                "API-ключ ExchangeRate-API не задан в переменной EXCHANGERATE_API_KEY"
            )

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/{key}/latest/"
            f"{self.config.BASE_CURRENCY}"
        )

        start_time = time.time()
        try:
            resp = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            elapsed_ms = int((time.time() - start_time) * 1000)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            raise ApiRequestError(f"Network error ExchangeRate-API: {exc}") from exc

        if data.get("result") == "error":
            err_type = data.get("error-type", "unknown")
            raise ApiRequestError(f"ExchangeRate-API error: {err_type}")

        rates = data.get("conversion_rates") or data.get("rates", {})
        result: dict[str, dict[str, Any]] = {}
        for fiat in self.config.FIAT_CURRENCIES:
            if fiat in rates:
                val = float(rates[fiat])
                pair_key = f"{fiat}_{self.config.BASE_CURRENCY}"
                result[pair_key] = {
                    "rate": (1.0 / val) if val > 0 else 0.0,
                    "source": "ExchangeRate-API",
                    "raw_id": fiat,
                    "request_ms": elapsed_ms,
                    "status_code": resp.status_code,
                }
        return result

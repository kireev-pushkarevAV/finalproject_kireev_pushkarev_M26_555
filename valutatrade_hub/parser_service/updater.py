from datetime import UTC, datetime
from typing import Any

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager

db = DatabaseManager()

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum,solana&vs_currencies=usd"
)
EXCHANGE_RATE_API_URL = "https://open.er-api.com/v6/latest/USD"


def fetch_crypto_rates() -> dict[str, float]:
    try:
        resp = requests.get(COINGECKO_URL, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return {
            "BTC_USD": float(data["bitcoin"]["usd"]),
            "ETH_USD": float(data["ethereum"]["usd"]),
            "SOL_USD": float(data["solana"]["usd"]),
        }
    except Exception as exc:
        raise ApiRequestError(f"CoinGecko API недоступен: {exc}") from exc


def fetch_fiat_rates() -> dict[str, float]:
    try:
        resp = requests.get(EXCHANGE_RATE_API_URL, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        rates = data.get("rates", {})
        eur_usd = 1.0 / float(rates["EUR"]) if "EUR" in rates else 1.08
        rub_usd = 1.0 / float(rates["RUB"]) if "RUB" in rates else 0.011
        gbp_usd = 1.0 / float(rates["GBP"]) if "GBP" in rates else 1.28
        return {
            "EUR_USD": eur_usd,
            "RUB_USD": rub_usd,
            "GBP_USD": gbp_usd,
            "USD_USD": 1.0,
        }
    except Exception as exc:
        raise ApiRequestError(f"ExchangeRate API недоступен: {exc}") from exc


@log_action("UPDATE_RATES")
def update_exchange_rates() -> dict[str, Any]:
    now_iso = datetime.now(UTC).isoformat()
    pairs: dict[str, dict[str, Any]] = {}

    fallback_pairs = {
        "BTC_USD": 65000.0,
        "ETH_USD": 3500.0,
        "SOL_USD": 145.0,
        "EUR_USD": 1.08,
        "RUB_USD": 0.011,
        "GBP_USD": 1.28,
        "USD_USD": 1.0,
    }

    try:
        crypto = fetch_crypto_rates()
    except ApiRequestError:
        crypto = {
            k: fallback_pairs[k] for k in ["BTC_USD", "ETH_USD", "SOL_USD"]
        }

    try:
        fiat = fetch_fiat_rates()
    except ApiRequestError:
        fiat = {
            k: fallback_pairs[k]
            for k in ["EUR_USD", "RUB_USD", "GBP_USD", "USD_USD"]
        }

    all_rates = {**crypto, **fiat}

    for pair_name, rate_val in all_rates.items():
        pairs[pair_name] = {
            "rate": rate_val,
            "updated_at": now_iso,
        }

    rates_payload = {
        "pairs": pairs,
        "last_refresh": now_iso,
    }

    db.write("RATES_FILE", rates_payload)

    exchange_list = [
        {"pair": k, "rate": v["rate"], "updated_at": v["updated_at"]}
        for k, v in pairs.items()
    ]
    db.write("EXCHANGE_RATES_FILE", exchange_list)

    return {
        "count": len(pairs),
        "updated_at": now_iso,
    }

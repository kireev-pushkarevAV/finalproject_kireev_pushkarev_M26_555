import os
from dataclasses import dataclass, field


@dataclass
class ParserConfig:
    EXCHANGERATE_API_KEY: str = field(
        default_factory=lambda: os.getenv(
            "EXCHANGERATE_API_KEY", "92b053daa1bc50d1de6f1155"
        )
    )
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple[str, ...] = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple[str, ...] = ("BTC", "ETH", "SOL")
    CRYPTO_ID_MAP: dict[str, str] = field(
        default_factory=lambda: {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
        }
    )

    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"
    REQUEST_TIMEOUT: int = 10

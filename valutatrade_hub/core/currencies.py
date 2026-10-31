from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name: str, code: str) -> None:
        clean_code = code.strip().upper()
        if not (2 <= len(clean_code) <= 5 and clean_code.isalpha()):
            raise ValueError("Код валюты должен содержать от 2 до 5 букв.")
        if not name or not name.strip():
            raise ValueError("Название валюты не может быть пустым.")

        self.name = name.strip()
        self.code = clean_code

    @abstractmethod
    def get_display_info(self) -> str:
        pass


class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        super().__init__(name, code)
        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float,
    ) -> None:
        super().__init__(name, code)
        self.algorithm = algorithm.strip()
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


_CURRENCY_REGISTRY: dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.20e11),
    "SOL": CryptoCurrency("Solana", "SOL", "PoH", 6.50e10),
}


def get_currency(code: str) -> Currency:
    clean_code = code.strip().upper()
    currency = _CURRENCY_REGISTRY.get(clean_code)
    if not currency:
        raise CurrencyNotFoundError(clean_code)
    return currency

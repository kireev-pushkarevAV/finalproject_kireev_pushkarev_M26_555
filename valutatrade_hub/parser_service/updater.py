import logging
from datetime import UTC, datetime
from typing import Any

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.decorators import log_action
from valutatrade_hub.parser_service.api_clients import (
    BaseApiClient,
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import save_rates_data

logger = logging.getLogger("valutatrade")


class RatesUpdater:
    def __init__(
        self,
        config: ParserConfig | None = None,
        clients: list[BaseApiClient] | None = None,
    ) -> None:
        self.config = config or ParserConfig()
        self.clients = clients or [
            CoinGeckoClient(self.config),
            ExchangeRateApiClient(self.config),
        ]

    @log_action("UPDATE_RATES")
    def run_update(self, source: str | None = None) -> dict[str, Any]:
        combined_rates: dict[str, dict[str, Any]] = {}
        now_iso = (
            datetime.now(UTC).replace(microsecond=0).isoformat() + "Z"
        )
        errors: list[str] = []

        clients_to_run = self.clients
        if source:
            src_lower = source.strip().lower()
            if "gecko" in src_lower or "crypto" in src_lower:
                clients_to_run = [
                    c for c in self.clients if isinstance(c, CoinGeckoClient)
                ]
            elif "exchange" in src_lower or "fiat" in src_lower:
                clients_to_run = [
                    c
                    for c in self.clients
                    if isinstance(c, ExchangeRateApiClient)
                ]

        print("INFO: Starting rates update...")
        for client in clients_to_run:
            c_name = (
                "CoinGecko"
                if isinstance(client, CoinGeckoClient)
                else "ExchangeRate-API"
            )
            try:
                rates = client.fetch_rates()
                combined_rates.update(rates)
                print(f"INFO: Fetching from {c_name}... OK ({len(rates)} rates)")
            except ApiRequestError as exc:
                err_msg = f"Failed to fetch from {c_name}: {exc}"
                print(f"ERROR: {err_msg}")
                logger.error(err_msg)
                errors.append(str(exc))

        if combined_rates:
            print(
                f"INFO: Writing {len(combined_rates)} rates to "
                f"{self.config.RATES_FILE_PATH}..."
            )
            save_rates_data(combined_rates, now_iso)

        if errors and not combined_rates:
            raise ApiRequestError(
                "Все источники недоступны. Проверьте сеть и API-ключ."
            )

        return {
            "rates_count": len(combined_rates),
            "errors_count": len(errors),
            "last_refresh": now_iso,
        }

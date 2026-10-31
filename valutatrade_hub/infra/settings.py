from pathlib import Path
from typing import Any


class SettingsLoader:
    _instance: "SettingsLoader | None" = None

    def __new__(cls) -> "SettingsLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_settings()
        return cls._instance

    def _init_settings(self) -> None:
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"

        self._config: dict[str, Any] = {
            "DATA_DIR": self.data_dir,
            "LOGS_DIR": self.logs_dir,
            "USERS_FILE": self.data_dir / "users.json",
            "PORTFOLIOS_FILE": self.data_dir / "portfolios.json",
            "RATES_FILE": self.data_dir / "rates.json",
            "EXCHANGE_RATES_FILE": self.data_dir / "exchange_rates.json",
            "RATES_TTL_SECONDS": 300,
            "BASE_CURRENCY": "USD",
            "LOG_FILE": self.logs_dir / "actions.log",
            "LOG_LEVEL": "INFO",
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def reload(self) -> None:
        self._init_settings()

import json
import os
from pathlib import Path
from typing import Any

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    _instance: "DatabaseManager | None" = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = SettingsLoader()
            cls._instance._ensure_storage()
        return cls._instance

    def _ensure_storage(self) -> None:
        data_dir: Path = self._settings.get("DATA_DIR")
        data_dir.mkdir(parents=True, exist_ok=True)

        defaults = [
            (self._settings.get("USERS_FILE"), []),
            (self._settings.get("PORTFOLIOS_FILE"), []),
            (self._settings.get("EXCHANGE_RATES_FILE"), []),
            (self._settings.get("RATES_FILE"), {"pairs": {}, "last_refresh": ""}),
        ]
        for file_path, default_data in defaults:
            if not file_path.exists():
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(default_data, f, indent=2)

    def read(self, key: str) -> Any:
        file_path: Path = self._settings.get(key)
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {} if "RATES" in key else []

    def write(self, key: str, data: Any) -> None:
        file_path: Path = self._settings.get(key)
        temp_file = file_path.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, file_path)

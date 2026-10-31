import json
import os
import secrets
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
RATES_FILE = DATA_DIR / "rates.json"


def ensure_storage_exists() -> None:
    """Проверяет наличие директории data и файлов хранилища."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    defaults = [
        (USERS_FILE, []),
        (PORTFOLIOS_FILE, []),
        (RATES_FILE, {"pairs": {}, "last_refresh": ""}),
    ]
    for file_path, default_data in defaults:
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2)


def read_json(file_path: Path) -> Any:
    """Безопасно читает JSON-файл."""
    ensure_storage_exists()
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return [] if file_path != RATES_FILE else {"pairs": {}}


def write_json(file_path: Path, data: Any) -> None:
    """Атомарно записывает данные в JSON через временный файл."""
    ensure_storage_exists()
    temp_file = file_path.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, file_path)


def generate_salt() -> str:
    """Генерирует случайную соль для хеширования пароля."""
    return secrets.token_hex(8)

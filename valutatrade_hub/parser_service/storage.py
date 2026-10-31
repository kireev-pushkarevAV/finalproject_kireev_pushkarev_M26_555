from datetime import UTC, datetime
from typing import Any

from valutatrade_hub.infra.database import DatabaseManager

db = DatabaseManager()


def save_rates_data(
    rates: dict[str, dict[str, Any]],
    now_iso: str | None = None,
) -> None:
    if now_iso is None:
        now_iso = (
            datetime.now(UTC).replace(microsecond=0).isoformat() + "Z"
        )

    current_rates = db.read("RATES_FILE")
    pairs_dict = (
        current_rates.get("pairs", {})
        if isinstance(current_rates, dict)
        else {}
    )

    for pair_key, info in rates.items():
        pairs_dict[pair_key] = {
            "rate": info["rate"],
            "updated_at": now_iso,
            "source": info["source"],
        }

    db.write("RATES_FILE", {"pairs": pairs_dict, "last_refresh": now_iso})

    history = db.read("EXCHANGE_RATES_FILE")
    if not isinstance(history, list):
        history = []

    for pair_key, info in rates.items():
        from_curr, to_curr = pair_key.split("_")
        record_id = f"{from_curr}_{to_curr}_{now_iso}"
        history.append(
            {
                "id": record_id,
                "from_currency": from_curr,
                "to_currency": to_curr,
                "rate": info["rate"],
                "timestamp": now_iso,
                "source": info["source"],
                "meta": {
                    "raw_id": info.get("raw_id", ""),
                    "request_ms": info.get("request_ms", 0),
                    "status_code": info.get("status_code", 200),
                },
            }
        )

    db.write("EXCHANGE_RATES_FILE", history)

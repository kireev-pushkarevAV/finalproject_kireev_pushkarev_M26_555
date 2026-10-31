from collections.abc import Callable
from functools import wraps
from typing import Any

from valutatrade_hub.logging_config import setup_logging

logger = setup_logging()


def log_action(action_name: str, verbose: bool = False) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                user = result.get("username") or result.get("user", "")
                currency = result.get("currency", "")
                amount = result.get("amount")
                rate = result.get("rate")

                parts = [f"{action_name.upper()}"]
                if user:
                    parts.append(f"user='{user}'")
                if currency:
                    parts.append(f"currency='{currency}'")
                if amount is not None:
                    parts.append(f"amount={amount:.4f}")
                if rate is not None:
                    parts.append(f"rate={rate:.2f} base='USD'")

                parts.append("result=OK")

                if verbose and "before" in result and "after" in result:
                    b_val = result["before"]
                    a_val = result["after"]
                    parts.append(f"context='balance: {b_val:.4f} -> {a_val:.4f}'")

                logger.info(" ".join(parts))
                return result
            except Exception as exc:
                err_type = type(exc).__name__
                logger.error(
                    f"{action_name.upper()} result=ERROR "
                    f"error_type={err_type} error_message='{exc}'"
                )
                raise exc

        return wrapper

    return decorator

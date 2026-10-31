from datetime import UTC, datetime
from typing import Any

from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.core.utils import (
    PORTFOLIOS_FILE,
    RATES_FILE,
    USERS_FILE,
    generate_salt,
    read_json,
    write_json,
)

_CURRENT_USER: User | None = None


def get_current_user() -> User | None:
    return _CURRENT_USER


def set_current_user(user: User | None) -> None:
    global _CURRENT_USER
    _CURRENT_USER = user


def load_rates() -> dict[str, Any]:
    data = read_json(RATES_FILE)
    return data.get("pairs", {}) if isinstance(data, dict) else {}


def get_exchange_rate(from_curr: str, to_curr: str) -> tuple[float, str]:
    from_c = from_curr.upper()
    to_c = to_curr.upper()

    if from_c == to_c:
        return 1.0, datetime.now(UTC).isoformat()

    pairs = load_rates()

    direct_pair = f"{from_c}_{to_c}"
    if direct_pair in pairs:
        return float(pairs[direct_pair]["rate"]), pairs[direct_pair]["updated_at"]

    reverse_pair = f"{to_c}_{from_c}"
    if reverse_pair in pairs:
        rate = 1.0 / float(pairs[reverse_pair]["rate"])
        return rate, pairs[reverse_pair]["updated_at"]

    to_usd_from = f"{from_c}_USD"
    to_usd_to = f"{to_c}_USD"
    if to_usd_from in pairs and to_usd_to in pairs:
        cross_rate = float(pairs[to_usd_from]["rate"]) / float(
            pairs[to_usd_to]["rate"]
        )
        return cross_rate, pairs[to_usd_from]["updated_at"]

    raise ValueError(f"Курс {from_c}→{to_c} недоступен. Повторите попытку позже.")


def register_user(username: str, password: str) -> dict[str, Any]:
    if not username or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым.")
    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов.")

    clean_name = username.strip()
    users_data = read_json(USERS_FILE)

    for entry in users_data:
        if entry["username"].lower() == clean_name.lower():
            raise ValueError(f"Имя пользователя '{clean_name}' уже занято")

    new_id = max([u["user_id"] for u in users_data], default=0) + 1
    salt = generate_salt()
    hashed_pwd = User.hash_password(password, salt)

    user = User(
        user_id=new_id,
        username=clean_name,
        hashed_password=hashed_pwd,
        salt=salt,
        registration_date=datetime.now(),
    )

    users_data.append(user.to_dict())
    write_json(USERS_FILE, users_data)

    portfolios_data = read_json(PORTFOLIOS_FILE)
    portfolios_data.append({"user_id": new_id, "wallets": {}})
    write_json(PORTFOLIOS_FILE, portfolios_data)

    return {"user_id": new_id, "username": clean_name}


def login_user(username: str, password: str) -> User:
    users_data = read_json(USERS_FILE)
    clean_name = username.strip()

    user_dict = next(
        (u for u in users_data if u["username"].lower() == clean_name.lower()),
        None,
    )
    if not user_dict:
        raise ValueError(f"Пользователь '{clean_name}' не найден")

    user = User(
        user_id=user_dict["user_id"],
        username=user_dict["username"],
        hashed_password=user_dict["hashed_password"],
        salt=user_dict["salt"],
        registration_date=datetime.fromisoformat(user_dict["registration_date"]),
    )

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    set_current_user(user)
    return user


def load_user_portfolio(user_id: int) -> Portfolio:
    portfolios_data = read_json(PORTFOLIOS_FILE)
    port_dict = next((p for p in portfolios_data if p["user_id"] == user_id), None)

    if not port_dict:
        return Portfolio(user_id=user_id, wallets={})

    wallets = {
        code: Wallet(currency_code=code, balance=info["balance"])
        for code, info in port_dict.get("wallets", {}).items()
    }
    return Portfolio(user_id=user_id, wallets=wallets)


def save_user_portfolio(portfolio: Portfolio) -> None:
    portfolios_data = read_json(PORTFOLIOS_FILE)
    updated = False
    for i, p in enumerate(portfolios_data):
        if p["user_id"] == portfolio.user_id:
            portfolios_data[i] = portfolio.to_dict()
            updated = True
            break
    if not updated:
        portfolios_data.append(portfolio.to_dict())
    write_json(PORTFOLIOS_FILE, portfolios_data)


def execute_buy(currency: str, amount: float) -> dict[str, Any]:
    user = get_current_user()
    if not user:
        raise PermissionError("Сначала выполните login")

    curr = currency.strip().upper()
    if not curr:
        raise ValueError("Код валюты не может быть пустым.")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    rate_to_usd, _ = get_exchange_rate(curr, "USD")
    cost_usd = amount * rate_to_usd

    portfolio = load_user_portfolio(user.user_id)
    wallet = portfolio.get_wallet(curr)
    before_balance = wallet.balance if wallet else 0.0

    if not wallet:
        wallet = portfolio.add_currency(curr)

    wallet.deposit(amount)
    save_user_portfolio(portfolio)

    return {
        "currency": curr,
        "amount": amount,
        "rate": rate_to_usd,
        "before": before_balance,
        "after": wallet.balance,
        "cost_usd": cost_usd,
    }


def execute_sell(currency: str, amount: float) -> dict[str, Any]:
    user = get_current_user()
    if not user:
        raise PermissionError("Сначала выполните login")

    curr = currency.strip().upper()
    if not curr:
        raise ValueError("Код валюты не может быть пустым.")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    portfolio = load_user_portfolio(user.user_id)
    wallet = portfolio.get_wallet(curr)

    if not wallet:
        raise ValueError(
            f"У вас нет кошелька '{curr}'. Добавьте валюту: "
            "она создаётся автоматически при первой покупке."
        )

    before_balance = wallet.balance
    wallet.withdraw(amount)

    rate_to_usd, _ = get_exchange_rate(curr, "USD")
    proceeds_usd = amount * rate_to_usd

    save_user_portfolio(portfolio)

    return {
        "currency": curr,
        "amount": amount,
        "rate": rate_to_usd,
        "before": before_balance,
        "after": wallet.balance,
        "proceeds_usd": proceeds_usd,
    }

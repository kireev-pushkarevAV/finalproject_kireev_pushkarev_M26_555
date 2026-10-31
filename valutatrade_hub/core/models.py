import hashlib
from datetime import datetime
from typing import Any


class User:
    """Класс пользователя системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime | None = None,
    ) -> None:
        self._user_id = user_id
        self._username = ""
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date or datetime.now()

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """Односторонний псевдо-хеш пароля с солью."""
        return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

    def change_password(self, new_password: str) -> None:
        """Изменяет пароль пользователя с валидацией длины и хешированием."""
        if not isinstance(new_password, str) or len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")
        self._hashed_password = self.hash_password(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        """Проверяет совпадение введенного пароля."""
        return self.hash_password(password, self._salt) == self._hashed_password

    def get_user_info(self) -> dict[str, Any]:
        """Возвращает публичную информацию о пользователе (без пароля и соли)."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def to_dict(self) -> dict[str, Any]:
        """Сериализация для сохранения в users.json."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }


class Wallet:
    """Кошелек пользователя для одной конкретной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым.")
        self.currency_code = currency_code.strip().upper()
        self._balance: float = 0.0
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом.")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """Пополнение баланса кошелька."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("'amount' должен быть положительным числом.")
        self._balance += float(amount)

    def withdraw(self, amount: float) -> None:
        """Снятие средств с проверкой доступного остатка."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("'amount' должен быть положительным числом.")
        if amount > self._balance:
            raise ValueError(
                f"Недостаточно средств: доступно {self._balance:.4f} "
                f"{self.currency_code}, требуется {amount:.4f} {self.currency_code}"
            )
        self._balance -= float(amount)

    def get_balance_info(self) -> str:
        """Вывод информации о текущем балансе."""
        return f"{self.currency_code}: {self._balance:.4f}"

    def to_dict(self) -> dict[str, Any]:
        """Сериализация для portfolios.json."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }


class Portfolio:
    """Управление всеми кошельками одного пользователя."""

    def __init__(
        self,
        user_id: int,
        wallets: dict[str, Wallet] | None = None,
        user: User | None = None,
    ) -> None:
        self._user_id = user_id
        self._user = user
        self._wallets: dict[str, Wallet] = wallets if wallets is not None else {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def user(self) -> User | None:
        return self._user

    @property
    def wallets(self) -> dict[str, Wallet]:
        """Возвращает поверхностную копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """Создает новый кошелек в портфеле, если его еще нет."""
        code = currency_code.strip().upper()
        if code in self._wallets:
            raise ValueError(f"Кошелек для валюты {code} уже существует.")
        new_wallet = Wallet(currency_code=code, balance=0.0)
        self._wallets[code] = new_wallet
        return new_wallet

    def get_wallet(self, currency_code: str) -> Wallet | None:
        """Возвращает объект Wallet по коду валюты."""
        return self._wallets.get(currency_code.strip().upper())

    def get_total_value(
        self,
        base_currency: str = "USD",
        exchange_rates: dict[str, float] | None = None,
    ) -> float:
        """Подсчитывает суммарную стоимость кошельков в базовой валюте."""
        base = base_currency.strip().upper()
        rates = exchange_rates or {"USD": 1.0}
        total = 0.0

        for code, wallet in self._wallets.items():
            if code == base:
                total += wallet.balance
            else:
                pair_direct = f"{code}_{base}"
                pair_reverse = f"{base}_{code}"

                if pair_direct in rates:
                    total += wallet.balance * rates[pair_direct]
                elif pair_reverse in rates and rates[pair_reverse] != 0:
                    total += wallet.balance * (1.0 / rates[pair_reverse])
                else:
                    raise ValueError(f"Не удалось получить курс для {code}→{base}")

        return total

    def to_dict(self) -> dict[str, Any]:
        """Сериализация для portfolios.json."""
        return {
            "user_id": self._user_id,
            "wallets": {
                code: {"balance": wallet.balance}
                for code, wallet in self._wallets.items()
            },
        }

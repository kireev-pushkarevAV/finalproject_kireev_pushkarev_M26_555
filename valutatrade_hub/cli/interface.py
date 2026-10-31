import argparse
import shlex
import sys

from prettytable import PrettyTable

from valutatrade_hub.core import usecases
from valutatrade_hub.core.exceptions import (
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.parser_service.updater import RatesUpdater

db = DatabaseManager()


def parse_line(line: str) -> list[str]:
    return shlex.split(line, posix=(sys.platform != "win32"))


def handle_register(args: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="register", add_help=False)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)

    try:
        parsed = parser.parse_args(args)
        result = usecases.register_user(parsed.username, parsed.password)
        print(
            f"Пользователь '{result['username']}' зарегистрирован "
            f"(id={result['user_id']}). Войдите: "
            f"login --username {result['username']} --password ****"
        )
    except (argparse.ArgumentError, SystemExit):
        print("Ошибка: укажите --username <str> и --password <str>")
    except ValueError as e:
        print(e)


def handle_login(args: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="login", add_help=False)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)

    try:
        parsed = parser.parse_args(args)
        res = usecases.login_user(parsed.username, parsed.password)
        print(f"Вы вошли как '{res['username']}'")
    except (argparse.ArgumentError, SystemExit):
        print("Ошибка: укажите --username <str> и --password <str>")
    except ValueError as e:
        print(e)


def handle_show_portfolio(args: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="show-portfolio", add_help=False)
    parser.add_argument("--base", default="USD")

    try:
        parsed = parser.parse_args(args)
        user = usecases.get_current_user()
        if not user:
            print("Сначала выполните login")
            return

        portfolio = usecases.load_user_portfolio(user.user_id)
        wallets = portfolio.wallets
        base = parsed.base.upper()

        if not wallets:
            print(f"Портфель пользователя '{user.username}' пуст.")
            return

        table = PrettyTable()
        table.field_names = [
            "Валюта",
            "Баланс",
            f"Курс к {base}",
            f"Стоимость ({base})",
        ]
        table.align["Валюта"] = "l"
        table.align["Баланс"] = "r"
        table.align[f"Курс к {base}"] = "r"
        table.align[f"Стоимость ({base})"] = "r"

        total_val = 0.0
        for code, wallet in wallets.items():
            rate, _ = usecases.get_exchange_rate(code, base)
            val_in_base = wallet.balance * rate
            total_val += val_in_base
            table.add_row(
                [
                    code,
                    f"{wallet.balance:.4f}",
                    f"{rate:.4f}",
                    f"{val_in_base:.2f}",
                ]
            )

        print(f"\nПортфель пользователя '{user.username}':")
        print(table)
        print(f"ИТОГО: {total_val:,.2f} {base}\n".replace(",", " "))
    except (argparse.ArgumentError, SystemExit):
        print("Ошибка параметров команды show-portfolio")
    except (CurrencyNotFoundError, ValueError) as e:
        print(e)


def handle_buy(args: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="buy", add_help=False)
    parser.add_argument("--currency", required=True)
    parser.add_argument("--amount", type=float, required=True)

    try:
        parsed = parser.parse_args(args)
        res = usecases.execute_buy(parsed.currency, parsed.amount)
        print(
            f"Покупка выполнена: {res['amount']:.4f} {res['currency']} "
            f"по курсу {res['rate']:.2f} USD/{res['currency']}"
        )
        print("Изменения в портфеле:")
        print(
            f"{res['currency']}: было {res['before']:.4f} → "
            f"стало {res['after']:.4f}"
        )
        print(
            f"Оценочная стоимость покупки: {res['cost_usd']:,.2f} USD".replace(
                ",", " "
            )
        )
    except (argparse.ArgumentError, SystemExit):
        print("Ошибка: используйте buy --currency <str> --amount <float>")
    except (PermissionError, ValueError, CurrencyNotFoundError) as e:
        print(e)


def handle_sell(args: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="sell", add_help=False)
    parser.add_argument("--currency", required=True)
    parser.add_argument("--amount", type=float, required=True)

    try:
        parsed = parser.parse_args(args)
        res = usecases.execute_sell(parsed.currency, parsed.amount)
        print(
            f"Продажа выполнена: {res['amount']:.4f} {res['currency']} "
            f"по курсу {res['rate']:.2f} USD/{res['currency']}"
        )
        print("Изменения в портфеле:")
        print(
            f"{res['currency']}: было {res['before']:.4f} → "
            f"стало {res['after']:.4f}"
        )
        print(
            f"Оценочная выручка: {res['proceeds_usd']:,.2f} USD".replace(
                ",", " "
            )
        )
    except (argparse.ArgumentError, SystemExit):
        print("Ошибка: используйте sell --currency <str> --amount <float>")
    except (
        PermissionError,
        ValueError,
        CurrencyNotFoundError,
        InsufficientFundsError,
    ) as e:
        print(e)


def handle_get_rate(args: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="get-rate", add_help=False)
    parser.add_argument("--from", dest="from_curr", required=True)
    parser.add_argument("--to", dest="to_curr", required=True)

    try:
        parsed = parser.parse_args(args)
        rate, updated_at = usecases.get_exchange_rate(
            parsed.from_curr, parsed.to_curr
        )
        rev_rate, _ = usecases.get_exchange_rate(
            parsed.to_curr, parsed.from_curr
        )

        rate_fmt = f"{rate:.8f}" if rate < 1 else f"{rate:.2f}"
        rev_rate_fmt = f"{rev_rate:.8f}" if rev_rate < 1 else f"{rev_rate:.2f}"

        print(
            f"Курс {parsed.from_curr.upper()}→{parsed.to_curr.upper()}: "
            f"{rate_fmt} (обновлено: {updated_at.replace('T', ' ')})"
        )
        print(
            f"Обратный курс {parsed.to_curr.upper()}→"
            f"{parsed.from_curr.upper()}: {rev_rate_fmt}"
        )
    except (argparse.ArgumentError, SystemExit):
        print("Ошибка: используйте get-rate --from <str> --to <str>")
    except (CurrencyNotFoundError, ValueError) as e:
        print(e)


def handle_update_rates(args: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="update-rates", add_help=False)
    parser.add_argument("--source", default=None)

    try:
        parsed = parser.parse_args(args)
        updater = RatesUpdater()
        res = updater.run_update(source=parsed.source)

        if res["errors_count"] > 0:
            print("Update completed with errors. Check logs/actions.log for details.")
        else:
            print(
                f"Update successful. Total rates updated: {res['rates_count']}. "
                f"Last refresh: {res['last_refresh']}"
            )
    except Exception as e:
        print(f"Ошибка обновления курсов: {e}")


def handle_show_rates(args: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="show-rates", add_help=False)
    parser.add_argument("--currency", default=None)
    parser.add_argument("--top", type=int, default=None)
    parser.add_argument("--base", default="USD")

    try:
        parsed = parser.parse_args(args)
        rates_data = db.read("RATES_FILE")
        pairs = rates_data.get("pairs", {}) if isinstance(rates_data, dict) else {}

        if not pairs:
            print(
                "Локальный кеш курсов пуст. Выполните 'update-rates', "
                "чтобы загрузить данные."
            )
            return

        last_refresh = rates_data.get("last_refresh", "N/A")
        print(f"Rates from cache (updated at {last_refresh}):")

        if parsed.currency:
            curr = parsed.currency.upper()
            found = False
            for pair, info in pairs.items():
                if pair.startswith(f"{curr}_") or pair.endswith(f"_{curr}"):
                    print(f"- {pair}: {info['rate']}")
                    found = True
            if not found:
                print(f"Курс для '{curr}' не найден в кеше.")
            return

        if parsed.top:
            crypto_pairs = [
                (pair, info)
                for pair, info in pairs.items()
                if info.get("source") == "CoinGecko"
            ]
            sorted_crypto = sorted(
                crypto_pairs, key=lambda x: x[1]["rate"], reverse=True
            )[: parsed.top]
            for pair, info in sorted_crypto:
                print(f"- {pair}: {info['rate']}")
            return

        for pair, info in sorted(pairs.items()):
            print(f"- {pair}: {info['rate']}")
    except (argparse.ArgumentError, SystemExit):
        print("Ошибка параметров команды show-rates")
    except Exception as e:
        print(f"Ошибка: {e}")


def run_cli() -> None:
    print("ValutaTrade Hub CLI запущен. Введите команду (или 'exit' для выхода):")
    commands = {
        "register": handle_register,
        "login": handle_login,
        "show-portfolio": handle_show_portfolio,
        "buy": handle_buy,
        "sell": handle_sell,
        "get-rate": handle_get_rate,
        "update-rates": handle_update_rates,
        "show-rates": handle_show_rates,
    }

    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue
            if line in ("exit", "quit"):
                break

            tokens = parse_line(line)
            cmd, cmd_args = tokens[0], tokens[1:]

            if cmd in commands:
                commands[cmd](cmd_args)
            else:
                print(
                    f"Неизвестная команда: '{cmd}'. Доступные: "
                    f"{', '.join(commands.keys())}, exit"
                )
        except (KeyboardInterrupt, EOFError):
            print("\nСеанс завершен.")
            break

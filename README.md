# ValutaTrade Hub

Консольная платформа для симуляции торговли валютами и криптовалютами с автономным микросервисом парсинга котировок в реальном времени.

## Архитектура системы

Проект состоит из двух ключевых компонентов:
1. Core Service — управление доменной логикой (пользователи, кошельки, портфели, исполнение сделок покупки/продажи, расчет суммарной стоимости в базовой валюте).
2. Parser Service — сбор актуальных котировок с внешних провайдеров (CoinGecko для криптовалют, ExchangeRate-API для фиатных валют), кэширование снимка в data/rates.json и ведение неизменяемого журнала замеров в data/exchange_rates.json.

### Структура проекта

```text
finalproject_kireev_pushkarev_M26_555/
├── data/
│   ├── users.json
│   ├── portfolios.json
│   ├── rates.json
│   └── exchange_rates.json
├── logs/
│   └── actions.log
├── valutatrade_hub/
│   ├── core/
│   │   ├── currencies.py
│   │   ├── exceptions.py
│   │   ├── models.py
│   │   ├── usecases.py
│   │   └── utils.py
│   ├── infra/
│   │   ├── database.py
│   │   └── settings.py
│   ├── parser_service/
│   │   ├── api_clients.py
│   │   ├── config.py
│   │   ├── scheduler.py
│   │   ├── storage.py
│   │   └── updater.py
│   ├── cli/
│   │   └── interface.py
│   ├── decorators.py
│   └── logging_config.py
├── main.py
├── pyproject.toml
└── uv.lock 
```
## Установка и запуск

Проект управляется через пакетный менеджер uv.

1. Клонирование и установка зависимостей:
git clone https://github.com/kireev-pushkarevAV/finalproject_kireev_pushkarev_M26_555.git
cd finalproject_kireev_pushkarev_M26_555
uv sync

2. Конфигурация окружения:
Для получения котировок фиатных валют используется ExchangeRate-API. Ключ задается через переменную окружения:

PowerShell (Windows):
$env:EXCHANGERATE_API_KEY="92b053daa1bc50d1de6f1155"

Bash (Linux / macOS):
export EXCHANGERATE_API_KEY="92b053daa1bc50d1de6f1155"

3. Запуск приложения:
uv run python main.py

4. Проверка качества кода:
uv run ruff check .

## Доступные команды CLI

* `update-rates [--source <coingecko|exchangerate>]` — обновление котировок из внешних API в локальный кэш и журнал.
* `show-rates [--currency <CODE>] [--top <N>] [--base <CODE>]` — просмотр актуальных курсов из кэша с фильтрацией.
* `register --username <str> --password <str>` — регистрация нового аккаунта (пароль от 4 символов).
* `login --username <str> --password <str>` — авторизация текущей сессии.
* `buy --currency <CODE> --amount <float>` — покупка указанного объема актива по курсу к USD.
* `sell --currency <CODE> --amount <float>` — продажа указанного объема актива.
* `show-portfolio [--base <CODE>]` — вывод сводной таблицы активов и балансов пользователя.
* `get-rate --from <CODE> --to <CODE>` — получение прямого и обратного курса между двумя валютами.
* `exit` — завершение сеанса.

## Демонстрация работы

> **Интерактивная запись консоли (веб-плеер):**  
> 🔗 [Посмотреть сценарий работы и обработку ошибок на asciinema.org](https://asciinema.org/a/g85lxepuCA1LSi9L)

Локальная запись сессии в формате asciinema v2 также доступна в репозитории: [`demo.cast`](demo.cast). Для воспроизведения в терминале:
```bash
asciinema play demo.cast
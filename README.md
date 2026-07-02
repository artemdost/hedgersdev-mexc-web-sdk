# mexc-web

> Сделано командой **[Hedgersdev](https://t.me/hedgersdev)**. Telegram: **[@hedgersdev](https://t.me/hedgersdev)**

Неофициальный Python-SDK для **MEXC Futures** на web-токене (`u_id` из браузера,
том самом, что использует торговый интерфейс биржи). API-ключи не нужны:
залогинился в браузере, скопировал токен, торгуешь из кода.

Что умеет: рынок, аккаунт и балансы, позиции, плечо и маржа, ордера (лимит,
маркет, post-only, IOC, FOK, батч, chase), плановые ордера, TP/SL,
трейлинг-стоп, STP-группы, данные аккаунта (email, uid), переводы между
кошельками (спот, фьючи, funding) и WebSocket (публичные каналы плюс приватные
пуши по ордерам и позициям).

## Установка

```bash
pip install "mexc-web @ git+https://github.com/mexicanchik/hedgersdev-mexc-web-sdk"
# с поддержкой WebSocket:
pip install "mexc-web[ws] @ git+https://github.com/mexicanchik/hedgersdev-mexc-web-sdk"
```

Зависимости: `requests` (обязательно) и `websocket-client` (для WS, опционально).

## Как получить web-токен

1. Войди в аккаунт на [MEXC](https://www.mexc.com/futures/BTC_USDT).
2. Открой раздел Futures.
3. ПКМ, Inspect, вкладка Application.
4. Слева Cookies, `https://www.mexc.com`.
5. Скопируй значение ключа `u_id`. Это и есть твой токен.

Токен живёт примерно 1-4 недели. Когда запросы начнут возвращать ошибку
авторизации, обнови его тем же способом и вызови `client.set_token(new_token)`.

Токен даёт полный доступ к торговле. Не коммить его, не публикуй, держи в `.env`
или переменной окружения.

## Быстрый старт

```python
import os
from mexc_web import MexcClient

client = MexcClient(os.environ["MEXC_TOKEN"])

# Публичные данные (токен не нужен)
print(client.market.ticker("BTC_USDT"))

# Кто я: email и uid аккаунта
print("email:", client.user.email())
print("uid:", client.user.uid())

# Баланс
for a in client.account.assets()["data"]:
    if a["equity"]:
        print(a["currency"], a["equity"])

# Открыть лонг: 1 контракт BTC_USDT, лимитка, изолированная, плечо 20
from mexc_web.rest.orders import OPEN_LONG, LIMIT, ISOLATED
resp = client.orders.create(
    "BTC_USDT", side=OPEN_LONG, vol=1, type=LIMIT,
    price=50000, open_type=ISOLATED, leverage=20,
)
order_id = resp["data"]["orderId"]

# Изменить и отменить
client.orders.change_limit_order(order_id, price=49500, vol=1)
client.orders.cancel([order_id])

# Позиции и плечо
print(client.positions.open())
client.positions.set_leverage(50, symbol="BTC_USDT", open_type=ISOLATED, position_type=1)
```

Ответы приходят как есть, в конверте MEXC `{"success", "code", "data", ...}`.
Если `success: false`, поднимается `MexcAPIError`.

## Пространства методов

| Namespace | Что внутри |
|-----------|------------|
| `client.market` | ping, contract detail, depth, klines, deals, ticker, funding, index/fair price, insurance fund |
| `client.user` | email, uid (digitalId), профиль (ucenter на `www.mexc.com`) |
| `client.wallet` | переводы между кошельками (спот/фьючи/funding), overview, balances |
| `client.account` | assets, asset, fee rate, tiered/30d fees, risk limits, zero-fee пары, profit rate, transfer records |
| `client.positions` | open/history, position mode, leverage, margin, auto-add-margin, close_all, reverse, funding records |
| `client.orders` | create/create_raw, batch, cancel/cancel_all, by-external, change/chase, get, open/history/closed, deals, fee details, in-flight count |
| `client.plan` | плановые (conditional) ордера: place/cancel/cancel_all/change/list |
| `client.tpsl` | take-profit / stop-loss: place/cancel/change/list/open_orders |
| `client.trailing` | трейлинг-стоп: place/cancel/change/list |
| `client.stp` | self-trade-prevention группы: list/current/create/update/delete |

Нужен метод, которого нет в обёртках? Есть прямой доступ:

```python
client.request("GET", "/private/account/assets")
client.request("POST", "/private/order/create", params={...})
```

## Переводы средств

### Вариант A: по web-токену, без API-ключа

Web-токен двигает средства между кошельками (MEXC авторизует его как cookie на
asset-платформе, ровно как кнопка "Transfer" в вебе). Всё прямо из `MexcClient`:

```python
client = MexcClient("YOUR_U_ID_TOKEN")

print(client.wallet.balances())     # {'USDT': {'spot': .., 'contract': .., 'otc': ..}}

client.wallet.spot_to_futures(25, "USDT")   # спот в фьючи
client.wallet.futures_to_spot(10, "USDT")   # фьючи в спот
client.wallet.spot_to_funding(5, "USDT")    # спот в funding (фиат/OTC)
client.wallet.funding_to_spot(5, "USDT")    # funding в спот

# произвольно; кошельки: MAIN=спот, SWAP=фьючи, OTC=funding/фиат, STOCK=сток
from mexc_web.rest.wallet import MAIN, SWAP, OTC
client.wallet.transfer("USDT", MAIN, OTC, 5)
```

Идентификаторы кошельков (проверено на живом аккаунте): `MAIN` (спот), `SWAP`
(фьючи), `OTC` (funding/фиат, сюда падают карты и фиат), `STOCK` (нужно открыть
счёт).

### Вариант B: по API-ключу (spot OpenAPI)

Тот же трансфер плюс депозит-адреса через API-ключ (HMAC), если так удобнее:

```python
from mexc_web import MexcSpotClient

spot = MexcSpotClient("API_KEY", "API_SECRET")   # нужно право Transfer/Wallet
print(spot.balances())
spot.transfer_to_futures(25, "USDT")
print(spot.transfer_history("SPOT", "FUTURES"))
print(spot.deposit_address("USDT", "TRC20"))
```

Вывод на внешний адрес (`capital/withdraw`) сознательно не добавлен.

## WebSocket

```python
from mexc_web import MexcWSClient

def on_msg(m):
    print(m.get("channel"), m.get("data"))

ws = MexcWSClient(on_message=on_msg, token=os.environ["MEXC_TOKEN"])
ws.connect()                 # фоновый поток; логин по токену автоматический
ws.sub_deal("BTC_USDT")      # публичные сделки
ws.sub_depth("BTC_USDT")     # стакан
ws.personal_filter(["order", "position"])   # приватные пуши
...
ws.close()
```

Приватный стрим можно поднять и по API-ключу:
`MexcWSClient(on_message=..., api_key=..., api_secret=...)`.

## Как устроена подпись

Web-API подписывает запросы по MD5-схеме (не HMAC, как в OpenAPI):

```
postfix   = md5(token + ts)[7:]
signature = md5(ts + serialized_body + postfix)
```

`ts` (мс) уходит в заголовок `x-mxc-nonce`, подпись в `x-mxc-sign`, сам токен в
`Authorization`. Тело сериализуется один раз и отправляется теми же байтами,
что были подписаны, иначе биржа вернёт "Confirming signature failed".

## Авторы

Разработано и поддерживается командой **Hedgersdev**.

Telegram-канал: **[@hedgersdev](https://t.me/hedgersdev)**, сигналы, инструменты
и апдейты. Если SDK пригодился, подпишись и поставь звезду репозиторию.

## Дисклеймер

Неофициальная библиотека, не аффилирована с MEXC. Использование web-токена на
твой страх и риск и в рамках правил биржи. Торговля деривативами связана с риском
потери средств. Лицензия MIT.

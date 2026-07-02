# mexc-web

> 🛠 Сделано командой **[Hedgersdev](https://t.me/hedgersdev)** — Telegram: **[@hedgersdev](https://t.me/hedgersdev)**

Неофициальный Python-SDK для **MEXC Futures** на **web-токене** (`u_id` из
браузера) — том самом, что использует торговый интерфейс биржи. Никаких
API-ключей: логинишься в браузере, копируешь токен, торгуешь из кода.

Покрыты **все** методы фьючерсного web-API: рынок, аккаунт и балансы, позиции,
плечо и маржа, ордера (лимит/маркет/пост-онли/IOC/FOK, батч, chase), плановые
(conditional) ордера, TP/SL, трейлинг-стоп, STP-группы, идентити (email/uid),
**переводы между кошельками** (спот/фьючи/funding) и WebSocket
(публичные каналы + приватные пуши по ордерам/позициям).

> 💸 Web-токен умеет и **двигать средства** между кошельками (спот ⇄ фьючи ⇄
> funding/фиат) — см. раздел «Переводы средств». Вывод на внешний адрес
> намеренно не включён.

---

## Установка

```bash
pip install "mexc-web @ git+https://github.com/artemdost/mexc-web-sdk"
# с поддержкой WebSocket:
pip install "mexc-web[ws] @ git+https://github.com/artemdost/mexc-web-sdk"
```

Зависимости: `requests` (обязательно), `websocket-client` (для WS, опционально).

---

## 🔑 Как получить web-токен

1. Войдите в аккаунт на [MEXC](https://www.mexc.com/futures/BTC_USDT).
2. Откройте раздел **Futures**.
3. `ПКМ → Inspect` → вкладка **Application**.
4. Слева **Cookies → https://www.mexc.com**.
5. Скопируйте значение ключа **`u_id`** — это и есть ваш токен.

> Токен живёт ~1–4 недели. Когда запросы начнут отдавать ошибку авторизации —
> обновите его тем же способом и вызовите `client.set_token(new_token)`.

**Токен = полный доступ к торговле. Не коммитьте его, не публикуйте, храните в
`.env` или переменной окружения.**

---

## Быстрый старт

```python
import os
from mexc_web import MexcClient

client = MexcClient(os.environ["MEXC_TOKEN"])

# Публичные данные (токен не нужен)
print(client.market.ticker("BTC_USDT"))

# Кто я: email + uid аккаунта
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

Все ответы возвращаются как есть — конверт MEXC `{"success", "code", "data", ...}`.
При `success: false` бросается `MexcAPIError`.

---

## Пространства методов

| Namespace            | Что покрывает                                                        |
|----------------------|---------------------------------------------------------------------|
| `client.market`      | ping, contract detail, depth, klines, deals, ticker, funding, index/fair price, insurance fund |
| `client.user`        | **email, uid (digitalId), профиль** — ucenter на `www.mexc.com` |
| `client.wallet`      | **переводы между кошельками** (спот/фьючи/funding) + overview/balances |
| `client.account`     | assets, asset, fee rate, tiered/30d fees, risk limits, zero-fee пары, profit rate, transfer records |
| `client.positions`   | open/history, position mode, leverage, margin, auto-add-margin, close_all, reverse, funding records |
| `client.orders`      | create/create_raw, batch, cancel/cancel_all, by-external, change/chase, get, open/history/closed, deals, fee details, in-flight count |
| `client.plan`        | плановые (conditional) ордера: place/cancel/cancel_all/change/list  |
| `client.tpsl`        | take-profit / stop-loss: place/cancel/change/list/open_orders       |
| `client.trailing`    | трейлинг-стоп: place/cancel/change/list                             |
| `client.stp`         | self-trade-prevention группы: list/current/create/update/delete     |

Нужен метод, которого нет? Есть escape-hatch:

```python
client.request("GET", "/private/account/assets")
client.request("POST", "/private/order/create", params={...})
```

---

## Переводы средств

### Вариант A — по web-токену (без API-ключа) ✅

Web-токен **умеет** двигать средства между кошельками — MEXC авторизует его как
cookie на asset-платформе (это же делает кнопка «Transfer» в вебе). Доступно
прямо из `MexcClient`:

```python
client = MexcClient("YOUR_U_ID_TOKEN")

print(client.wallet.balances())     # {'USDT': {'spot': .., 'contract': .., 'otc': ..}}

client.wallet.spot_to_futures(25, "USDT")   # спот → фьючи
client.wallet.futures_to_spot(10, "USDT")   # фьючи → спот
client.wallet.spot_to_funding(5, "USDT")    # спот → funding (фиат/OTC)
client.wallet.funding_to_spot(5, "USDT")    # funding → спот

# произвольно; кошельки: MAIN=спот, SWAP=фьючи, OTC=funding/фиат, STOCK=сток
from mexc_web.rest.wallet import MAIN, SWAP, OTC
client.wallet.transfer("USDT", MAIN, OTC, 5)
```

Идентификаторы кошельков (проверено вживую): `MAIN` (спот), `SWAP` (фьючи),
`OTC` (**funding / фиат** — сюда падают карты/фиат), `STOCK` (нужно открыть счёт).

### Вариант B — по API-ключу (spot OpenAPI)

Тот же трансфер + депозит-адреса через API-ключ (HMAC), если нужно:

```python
from mexc_web import MexcSpotClient

spot = MexcSpotClient("API_KEY", "API_SECRET")   # нужно право Transfer/Wallet
print(spot.balances())
spot.transfer_to_futures(25, "USDT")
print(spot.transfer_history("SPOT", "FUTURES"))
print(spot.deposit_address("USDT", "TRC20"))
```

> Внешний вывод (`capital/withdraw`) намеренно не включён; при необходимости добавим.

---

## WebSocket

```python
from mexc_web import MexcWSClient

def on_msg(m):
    print(m.get("channel"), m.get("data"))

ws = MexcWSClient(on_message=on_msg, token=os.environ["MEXC_TOKEN"])
ws.connect()                 # фоновый поток; login по токену — автоматически
ws.sub_deal("BTC_USDT")      # публичные сделки
ws.sub_depth("BTC_USDT")     # стакан
ws.personal_filter(["order", "position"])   # приватные пуши
...
ws.close()
```

Приватный стрим можно поднять и по API-ключу: `MexcWSClient(on_message=..., api_key=..., api_secret=...)`.

---

## Как это работает (подпись)

Web-API подписывает запросы MD5-схемой (не HMAC, как OpenAPI):

```
postfix   = md5(token + ts)[7:]
signature = md5(ts + serialized_body + postfix)
```

`ts` (мс) уходит в заголовок `x-mxc-nonce`, подпись — в `x-mxc-sign`, сам токен —
в `Authorization`. Тело сериализуется один раз и отправляется теми же байтами,
что были подписаны, — иначе биржа вернёт «Confirming signature failed».

---

## Авторы

Разработано и поддерживается командой **Hedgersdev**.

📢 Telegram-канал: **[@hedgersdev](https://t.me/hedgersdev)** — сигналы, инструменты и апдейты.

Если SDK пригодился — подпишись и закинь ⭐ репозиторию.

---

## Дисклеймер

Неофициальная библиотека, не аффилирована с MEXC. Использование web-токена —
на ваш страх и риск и в рамках правил биржи. Торговля деривативами сопряжена с
риском потери средств. Лицензия — MIT.

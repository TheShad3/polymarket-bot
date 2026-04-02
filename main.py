import requests
import time
import os

# Telegram
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Минимальная сумма сделки для уведомления
MIN_SIZE = 500

# Кошельки, за которыми нужно следить
WATCH_WALLETS = [
    "0x7f3c8979d0afa00007bae4747d5347122af05613",
    "0xd5ccdf772f795547e299de57f47966e24de8dea4",
    "0xc2e7800b5af46e6093872b177b7a5e7f0563be51",
    "0x019782cab5d844f02bafb71f512758be78579f3c",
    "0x07b8e44b90cc3e91b8d5fe60ea810d2534638e25",
    "0xFc2F4f50ce2F6045d35558A5E2D8d4b2aC6610c7",
    "0xbad457dc633bbb7b6cbe09dd5867a5e8e597acd7"
]

# URL Polymarket
URL = "https://clob.polymarket.com/trades?limit=20"

# Сохраняем уже отправленные сделки
seen_trades = set()


def send_message(text):
    """Отправка сообщения в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Ошибка отправки:", e)


def fetch_trades():
    """Получение последних сделок с Polymarket"""
    try:
        res = requests.get(URL, timeout=10)
        data = res.json()

        if isinstance(data, dict):
            return data.get("data", [])
        elif isinstance(data, list):
            return data
        else:
            return []
    except Exception as e:
        print("Ошибка загрузки:", e)
        return []


def main():
    print("Бот запущен...")

    while True:
        trades = fetch_trades()
        print(f"Получено сделок: {len(trades)}")  # Для логов Railway

        for t in trades:
            if not isinstance(t, dict):
                continue

            trade_id = t.get("id")
            trader = t.get("trader")
            market = t.get("market", "unknown")
            size = t.get("size", 0)
            price = t.get("price", 0)

            if not trade_id or trade_id in seen_trades:
                continue

            # Фильтр по кошелькам и сумме
            if trader not in WATCH_WALLETS:
                continue
            if size < MIN_SIZE:
                continue

            # Формируем сообщение
            text = f"""
🔥 КИТ-СДЕЛКА

👛 Трейдер: {trader}
📊 Событие: {market}
💰 Сумма: ${size}
📈 Цена: {price}
🔗 https://polymarket.com/market/{market.replace(' ', '-')}
"""

            send_message(text)
            seen_trades.add(trade_id)

        time.sleep(10)


if __name__ == "__main__":
    main()

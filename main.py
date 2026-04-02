import requests
import time
import os

# Telegram
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Минимальная сумма сделки
MIN_SIZE = 500

# Кошельки для отслеживания
WATCH_WALLETS = [
    "0x7f3c8979d0afa00007bae4747d5347122af05613",
    "0xd5ccdf772f795547e299de57f47966e24de8dea4",
    "0xc2e7800b5af46e6093872b177b7a5e7f0563be51",
    "0x019782cab5d844f02bafb71f512758be78579f3c",
    "0x07b8e44b90cc3e91b8d5fe60ea810d2534638e25",
    "0xFc2F4f50ce2F6045d35558A5E2D8d4b2aC6610c7",
    "0xbad457dc633bbb7b6cbe09dd5867a5e8e597acd7"
]

# Ключевые слова геополитики
KEYWORDS = [
    "Trump", "Biden", "Russia", "Ukraine", "China", "war", "election",
    "international", "us-foreign-policy", "ukraine-war", "middle-east",
    "red-sea", "houthi", "taiwan", "eu-politics", "uk-politics",
    "us-congress", "white-house", "administration", "federal-reserve",
    "interest-rates", "supreme-court", "trade-wars", "crypto-policy",
    "sanctions", "energy-policy"
]

# URL Polymarket
URL = "https://clob.polymarket.com/trades?limit=50"

# История для аномалий
seen_trades = set()
market_activity = {}  # {market: [sizes]}


def send_message(text):
    """Отправка сообщения в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Ошибка отправки:", e)


def fetch_trades():
    """Получение последних сделок"""
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


def contains_keyword(text):
    """Проверка, содержит ли текст ключевые слова"""
    if not text:
        return False
    text = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text:
            return True
    return False


def main():
    print("Бот запущен...")

    while True:
        trades = fetch_trades()
        print(f"Получено сделок: {len(trades)}")

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

            # Фильтр кошельков и суммы
            if trader not in WATCH_WALLETS:
                continue
            if size < MIN_SIZE:
                continue

            # Фильтр ключевых слов по событию
            if not contains_keyword(market):
                continue

            # Проверка аномалий: сохраняем последние размеры по рынку
            market_activity.setdefault(market, []).append(size)
            recent_sizes = market_activity[market][-3:]  # последние 3 сделки

            anomaly = ""
            if len(recent_sizes) >= 3 and all(s >= MIN_SIZE for s in recent_sizes):
                anomaly = "⚡ КИТОВСКАЯ АКТИВНОСТЬ!"

            # Формирование сообщения
            text = f"""
🔥 СДЕЛКА

👛 Трейдер: {trader}
📊 Событие: {market}
💰 Сумма: ${size}
📈 Цена: {price}
{anomaly}
🔗 https://polymarket.com/market/{market.replace(' ', '-')}
"""

            send_message(text)
            seen_trades.add(trade_id)

        time.sleep(10)


if __name__ == "__main__":
    main()

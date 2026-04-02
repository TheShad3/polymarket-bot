import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

seen_trades = set()

URL = "https://clob.polymarket.com/trades?limit=20"


def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text
        })
    except Exception as e:
        print("Ошибка отправки:", e)


def fetch_trades():
    try:
        res = requests.get(URL, timeout=10)
        data = res.json()

        # 👇 корректно извлекаем сделки
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

        for t in trades:
            # 👇 защита от кривых данных
            if not isinstance(t, dict):
                continue

            trade_id = t.get("id")

            if not trade_id:
                continue

            if trade_id not in seen_trades:
                text = f"""
🔥 СДЕЛКА

👛 {t.get('trader', 'unknown')}
📊 {t.get('market', 'unknown')}
💰 {t.get('size', '0')}
📈 {t.get('price', '0')}
"""

                send_message(text)
                seen_trades.add(trade_id)

        time.sleep(10)


if __name__ == "__main__":
    main()

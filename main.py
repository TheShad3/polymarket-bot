import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

seen_trades = set()

URL = "https://clob.polymarket.com/trades?limit=20"

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text
    })

def fetch_trades():
    try:
        res = requests.get(URL, timeout=10)
        data = res.json()
        return data
    except Exception as e:
        print("Ошибка:", e)
        return []

def main():
    print("Бот запущен...")

    while True:
        trades = fetch_trades()

        for t in trades:
            trade_id = t.get("id")

            if trade_id not in seen_trades:
                text = f"""
🔥 СДЕЛКА

👛 {t.get('trader')}
📊 {t.get('market')}
💰 {t.get('size')}
📈 {t.get('price')}
"""
                send_message(text)
                seen_trades.add(trade_id)

        time.sleep(10)

if __name__ == "__main__":
    main()

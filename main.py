import os
import time
import requests

TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

MIN_VOLUME = 20000
DELTA_THRESHOLD = 3000  # накопленный рост

history = {}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=10)
    except Exception as e:
        print("Ошибка TG:", e)

def fetch_markets():
    url = "https://gamma-api.polymarket.com/markets?limit=50"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Ошибка API:", e)
        return []

def main():
    print("Бот запущен...")

    while True:
        markets = fetch_markets()
        print(f"Маркетов: {len(markets)}")

        sent = 0

        for m in markets:
            market_id = m.get("id")
            title = m.get("question", "Unknown")
            volume = float(m.get("volume", 0))
            end_date = m.get("endDate", "")

            if not end_date or int(end_date[:4]) < 2024:
                continue

            if market_id not in history:
                history[market_id] = []
            
            history[market_id].append(volume)

            # храним только последние 5 значений (~2-3 минуты)
            if len(history[market_id]) > 5:
                history[market_id].pop(0)

            if len(history[market_id]) < 5:
                continue

            delta = history[market_id][-1] - history[market_id][0]

            print(title, volume, f"Δ5m {delta}")

            if volume >= MIN_VOLUME and delta >= DELTA_THRESHOLD:
                msg = (
                    f"🚀 НАКОПЛЕНИЕ ОБЪЁМА\n\n"
                    f"📊 {title}\n"
                    f"💰 Объем: {int(volume):,}$\n"
                    f"⚡ Рост за время: +{int(delta):,}$"
                )

                send_telegram(msg)
                sent += 1

        print(f"Отправлено: {sent}")
        time.sleep(30)

if __name__ == "__main__":
    main()

import os
import time
import requests

TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

MIN_VOLUME = 50000
DELTA_THRESHOLD = 10000  # прирост объема для сигнала

seen = set()
last_volumes = {}

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

            old_volume = last_volumes.get(market_id, volume)
            delta = volume - old_volume

            last_volumes[market_id] = volume

            print(title, volume, f"Δ {delta}")

            # 🔥 СИГНАЛ ТОЛЬКО ПРИ РОСТЕ
            if volume >= MIN_VOLUME and delta >= DELTA_THRESHOLD:
                msg = (
                    f"🚀 РОСТ ОБЪЁМА\n\n"
                    f"📊 {title}\n"
                    f"💰 Объем: {int(volume):,}$\n"
                    f"⚡ Прирост: +{int(delta):,}$"
                )

                send_telegram(msg)
                sent += 1

        print(f"Отправлено: {sent}")
        time.sleep(30)

if __name__ == "__main__":
    main()

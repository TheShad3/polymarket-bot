import os
import time
import requests

TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

MIN_VOLUME = 10000
DELTA_THRESHOLD = 2000

history = {}
sent_recent = set()

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
    print("БОТ ЗАПУЩЕН 🚀")

    while True:
        markets = fetch_markets()
        print(f"Маркетов: {len(markets)}")

        sent = 0

        for m in markets:
            market_id = m.get("id")
            title = m.get("question", "No title")

            try:
                volume = float(m.get("volume") or 0)
            except:
                volume = 0

            # -------------------
            # HISTORY
            # -------------------
            if market_id not in history:
                history[market_id] = []

            history[market_id].append(volume)

            if len(history[market_id]) > 6:
                history[market_id].pop(0)

            delta = 0
            if len(history[market_id]) >= 6:
                delta = history[market_id][-1] - history[market_id][0]

            print(f"{title} | {int(volume)} | Δ {int(delta)}")

            # -------------------
            # 🚀 СИГНАЛ РОСТА (главный)
            # -------------------
            if volume >= MIN_VOLUME and delta >= DELTA_THRESHOLD:
                msg = (
                    f"🚀 РОСТ ОБЪЁМА\n\n"
                    f"{title}\n"
                    f"💰 {int(volume):,}$\n"
                    f"⚡ +{int(delta):,}$"
                )

                send_telegram(msg)
                sent += 1
                continue

            # -------------------
            # 📊 ТОП РЫНКИ (редко)
            # -------------------
            if volume >= 50000 and market_id not in sent_recent:
                msg = (
                    f"📊 АКТИВНЫЙ РЫНОК\n\n"
                    f"{title}\n"
                    f"💰 {int(volume):,}$"
                )

                send_telegram(msg)
                sent_recent.add(market_id)
                sent += 1

        # очищаем, чтобы не залипало
        if len(sent_recent) > 200:
            sent_recent.clear()

        print(f"Отправлено: {sent}")
        print("-" * 40)

        time.sleep(30)

if __name__ == "__main__":
    main()

import os
import time
import requests

# ----------------------------
# ENV
# ----------------------------
TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

# ----------------------------
# SETTINGS
# ----------------------------
MIN_VOLUME = 50000
seen = set()

# ----------------------------
# TELEGRAM SEND (HTTP)
# ----------------------------
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=10)
    except Exception as e:
        print("Ошибка TG:", e)

# ----------------------------
# FETCH MARKETS
# ----------------------------
def fetch_markets():
    url = "https://gamma-api.polymarket.com/markets?limit=50"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Ошибка API:", e)
        return []

# ----------------------------
# MAIN
# ----------------------------
def main():
    print("Бот запущен...")

    while True:
        markets = fetch_markets()
        print(f"Маркетов: {len(markets)}")

        sent = 0

        for m in markets:
            market_id = m.get("id")

            if market_id in seen:
                continue

            seen.add(market_id)

            title = m.get("question", "Unknown")
            volume = float(m.get("volume", 0))
            end_date = m.get("endDate", "")

            # ❗ убираем старые рынки
            if "2020" in end_date:
                continue

            print(title, volume)

            if volume >= MIN_VOLUME:
                msg = (
                    f"🔥 Активный рынок\n\n"
                    f"📊 {title}\n"
                    f"💰 Объем: {int(volume):,}$"
                )

                send_telegram(msg)
                sent += 1

        print(f"Отправлено: {sent}")
        time.sleep(30)

if __name__ == "__main__":
    main()

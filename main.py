import os
import time
import requests
import telegram

# ----------------------------
# ENV
# ----------------------------
TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = int(os.getenv("TG_CHAT_ID"))

bot = telegram.Bot(token=TOKEN)

# ----------------------------
# SETTINGS
# ----------------------------
MIN_VOLUME = 50000  # фильтр объема
seen = set()

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
        print("Ошибка:", e)
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
            end_date = m.get("endDate")

            # ❗ фильтр старых рынков
            if not end_date or "2020" in end_date:
                continue

            print(title, volume)

            if volume >= MIN_VOLUME:
                msg = (
                    f"🔥 Активный рынок\n\n"
                    f"📊 {title}\n"
                    f"💰 Объем: {volume:,.0f}$"
                )

                try:
                    bot.send_message(chat_id=CHAT_ID, text=msg)
                    sent += 1
                except Exception as e:
                    print("Ошибка отправки:", e)

        print(f"Отправлено: {sent}")
        time.sleep(30)

if __name__ == "__main__":
    main()

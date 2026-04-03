import os
import time
import requests
from telegram import Bot

# ----------------------------
# ENV
# ----------------------------
TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = int(os.getenv("TG_CHAT_ID"))

bot = Bot(token=TOKEN)

# ----------------------------
# SETTINGS
# ----------------------------
MIN_AMOUNT = 20
seen = set()

# ----------------------------
# FETCH EVENTS
# ----------------------------
def fetch_events():
    url = "https://gamma-api.polymarket.com/events?limit=20"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Ошибка events:", e)
        return []

# ----------------------------
# FETCH TRADES ПО EVENT
# ----------------------------
def fetch_trades(event_id):
    url = f"https://gamma-api.polymarket.com/events/{event_id}/activity"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Ошибка trades:", e)
        return []

# ----------------------------
# MAIN
# ----------------------------
def main():
    print("Бот запущен...")

    while True:
        events = fetch_events()
        print(f"Получено событий: {len(events)}")

        sent = 0

        for e in events:
            event_id = e.get("id")
            title = e.get("title", "Unknown")

            trades = fetch_trades(event_id)

            for t in trades:
                if t.get("type") != "trade":
                    continue

                trade_id = t.get("id")
                if trade_id in seen:
                    continue

                seen.add(trade_id)

                wallet = t.get("user")
                amount = float(t.get("size", 0))

                print(f"{wallet} | {amount} | {title}")

                if amount >= MIN_AMOUNT:
                    msg = (
                        f"🔥 Сделка\n\n"
                        f"👛 {wallet}\n"
                        f"💰 {amount}$\n"
                        f"📊 {title}"
                    )

                    try:
                        bot.send_message(chat_id=CHAT_ID, text=msg)
                        sent += 1
                    except Exception as e:
                        print("Ошибка отправки:", e)

        print(f"Отправлено: {sent}")
        time.sleep(15)

if __name__ == "__main__":
    main()

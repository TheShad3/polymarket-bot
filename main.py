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
# FETCH (РАБОЧИЙ ENDPOINT)
# ----------------------------
def fetch_trades():
    url = "https://gamma-api.polymarket.com/events/trades?limit=50"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Ошибка загрузки:", e)
        return []

# ----------------------------
# MAIN LOOP
# ----------------------------
def main():
    print("Бот запущен...")

    while True:
        trades = fetch_trades()
        print(f"Получено сделок: {len(trades)}")

        sent = 0

        for t in trades:
            trade_id = t.get("id")
            if trade_id in seen:
                continue

            seen.add(trade_id)

            wallet = t.get("user")
            amount = float(t.get("size", 0))
            title = t.get("title", "Unknown")

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
        time.sleep(10)

if __name__ == "__main__":
    main()

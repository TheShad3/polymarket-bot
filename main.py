import os
import time
import requests
from telegram import Bot

TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = int(os.getenv("TG_CHAT_ID"))

bot = Bot(token=TOKEN)

MIN_AMOUNT = 20
seen = set()

def fetch_trades():
    url = "https://api.dune.com/api/v1/query/3368552/results"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("result", {}).get("rows", [])
    except Exception as e:
        print("Ошибка:", e)
        return []

def main():
    print("Бот запущен...")

    while True:
        trades = fetch_trades()
        print(f"Получено: {len(trades)}")

        sent = 0

        for t in trades:
            trade_id = t.get("tx_hash")
            if trade_id in seen:
                continue

            seen.add(trade_id)

            wallet = t.get("trader")
            amount = float(t.get("amount_usd", 0))
            market = t.get("market")

            print(wallet, amount, market)

            if amount >= MIN_AMOUNT:
                msg = (
                    f"🔥 Крупная сделка\n\n"
                    f"👛 {wallet}\n"
                    f"💰 {amount}$\n"
                    f"📊 {market}"
                )

                try:
                    bot.send_message(chat_id=CHAT_ID, text=msg)
                    sent += 1
                except Exception as e:
                    print("Ошибка отправки:", e)

        print(f"Отправлено: {sent}")
        time.sleep(20)

if __name__ == "__main__":
    main()

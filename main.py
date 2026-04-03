import os
import time
import requests
from telegram import Bot
from datetime import datetime, timedelta, timezone

# ----------------------------
# Переменные окружения
# ----------------------------
TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("Укажи TG_BOT_TOKEN и TG_CHAT_ID в Railway")

CHAT_ID = int(CHAT_ID)
bot = Bot(token=TOKEN)

# ----------------------------
# Настройки
# ----------------------------
MIN_AMOUNT = 20  # минимальная сумма для сигнала

# защита от дублей
seen_trades = set()

# ----------------------------
# Получение сделок (CLOB API)
# ----------------------------
def fetch_trades():
    url = "https://clob.polymarket.com/trades"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("trades", [])
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return []

# ----------------------------
# Основной цикл
# ----------------------------
def main():
    print("Бот запущен...")

    while True:
        trades = fetch_trades()
        print(f"Получено сделок: {len(trades)}")

        signals_sent = 0

        for t in trades:
            if not isinstance(t, dict):
                continue

            trade_id = t.get("id")
            if trade_id in seen_trades:
                continue

            seen_trades.add(trade_id)

            wallet = t.get("traderId")
            amount = float(t.get("amount", 0))
            title = t.get("marketTitle", "Unknown")

            # ЛОГ ВСЕХ СДЕЛОК
            print(f"{wallet} | {amount} | {title}")

            # ПРОСТОЙ ФИЛЬТР
            if amount >= MIN_AMOUNT:
                msg = (
                    f"🔥 Сделка\n\n"
                    f"👛 Кошелек: {wallet}\n"
                    f"💰 Сумма: {amount}\n"
                    f"📊 Маркет: {title}\n"
                )

                try:
                    bot.send_message(chat_id=CHAT_ID, text=msg)
                    signals_sent += 1
                except Exception as e:
                    print(f"Ошибка отправки: {e}")

        print(f"Отправлено сигналов: {signals_sent}")
        time.sleep(10)


if __name__ == "__main__":
    main()

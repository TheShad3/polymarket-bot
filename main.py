import os
import time
import requests

TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

history = {}
sent_recent = set()

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=10)

        print("TG STATUS:", r.status_code)
        print("TG RESPONSE:", r.text)

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

        if not markets:
            time.sleep(30)
            continue

        # 📊 смотрим максимальный объем
        try:
            max_vol = max([float(m.get("volume") or 0) for m in markets])
            print("MAX VOLUME:", int(max_vol))
        except:
            pass

        sent = 0

        for m in markets:
            market_id = m.get("id")
            title = m.get("question", "No title")

            # безопасный парсинг объема
            try:
                volume = float(m.get("volume") or 0)
            except:
                volume = 0

            # -------------------
            # HISTORY (для будущего роста)
            # -------------------
            if market_id not in history:
                history[market_id] = []

            history[market_id].append(volume)

            if len(history[market_id]) > 5:
                history[market_id].pop(0)

            delta = 0
            if len(history[market_id]) >= 5:
                delta = history[market_id][-1] - history[market_id][0]

            print(f"{title} | {int(volume)} | Δ {int(delta)}")

            # -------------------
            # 🔥 ГАРАНТИРОВАННЫЙ СИГНАЛ (fallback)
            # -------------------
            if market_id not in sent_recent:
                msg = (
                    f"📊 РЫНОК\n\n"
                    f"{title}\n"
                    f"💰 Объем: {int(volume):,}$"
                )

                send_telegram(msg)

                sent_recent.add(market_id)
                sent += 1

        # очищаем, чтобы снова слал через время
        if len(sent_recent) > 100:
            sent_recent.clear()

        print(f"Отправлено: {sent}")
        print("-" * 40)

        time.sleep(30)

if __name__ == "__main__":
    main()

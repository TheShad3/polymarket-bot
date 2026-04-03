import os
import time
import requests

TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

# 🔥 ЗАНИЖЕННЫЕ ПОРОГИ (чтобы сигналы были)
MIN_VOLUME = 5000
DELTA_THRESHOLD = 500

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
    print("Бот запущен...")

    while True:
        markets = fetch_markets()
        print(f"Маркетов: {len(markets)}")

        if not markets:
            time.sleep(30)
            continue

        # 🔥 СМОТРИМ МАКС ОБЪЕМ (для отладки)
        try:
            max_vol = max([float(m.get("volume", 0)) for m in markets])
            print("MAX VOLUME:", int(max_vol))
        except:
            pass

        sent = 0

        for m in markets:
            market_id = m.get("id")
            title = m.get("question", "Unknown")
            volume = float(m.get("volume", 0))
            end_date = m.get("endDate", "")

            # фильтр по дате (чтобы не было старых рынков)
            if not end_date:
                continue

            try:
                if int(end_date[:4]) < 2024:
                    continue
            except:
                continue

            # -------------------
            # HISTORY
            # -------------------
            if market_id not in history:
                history[market_id] = []

            history[market_id].append(volume)

            if len(history[market_id]) > 5:
                history[market_id].pop(0)

            if len(history[market_id]) >= 5:
                delta = history[market_id][-1] - history[market_id][0]
            else:
                delta = 0

            print(f"{title} | {int(volume)} | Δ {int(delta)}")

            # -------------------
            # 🚀 СИГНАЛ РОСТА
            # -------------------
            if volume >= MIN_VOLUME and delta >= DELTA_THRESHOLD:
                msg = (
                    f"🚀 РОСТ ОБЪЁМА\n\n"
                    f"📊 {title}\n"
                    f"💰 {int(volume):,}$\n"
                    f"⚡ +{int(delta):,}$"
                )

                send_telegram(msg)
                sent += 1
                continue

            # -------------------
            # 📊 FALLBACK (ТОП РЫНКИ)
            # -------------------
            if volume >= 15000 and market_id not in sent_recent:
                msg = (
                    f"📊 ТОП РЫНОК\n\n"
                    f"{title}\n"
                    f"💰 Объем: {int(volume):,}$"
                )

                send_telegram(msg)
                sent_recent.add(market_id)
                sent += 1

        # 🔥 ЧИСТИМ, чтобы снова слал через время
        if len(sent_recent) > 100:
            sent_recent.clear()

        print(f"Отправлено: {sent}")
        print("-" * 40)

        time.sleep(30)

if __name__ == "__main__":
    main()

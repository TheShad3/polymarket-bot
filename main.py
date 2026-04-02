import requests
import time
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import random

# Telegram
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Порог суммы сделки
MIN_SIZE = 500

# Интервал для топа активности (минут)
TOP_INTERVAL_MIN = 10
# Период активности (часов)
HOURS_ACTIVITY = 1

# Последние N сделок для расчета вероятности и тренда
N_PROB = 10

# Кошельки для отслеживания
WATCH_WALLETS = [
    "0x7f3c8979d0afa00007bae4747d5347122af05613",
    "0xd5ccdf772f795547e299de57f47966e24de8dea4",
    "0xc2e7800b5af46e6093872b177b7a5e7f0563be51",
    "0x019782cab5d844f02bafb71f512758be78579f3c",
    "0x07b8e44b90cc3e91b8d5fe60ea810d2534638e25",
    "0xFc2F4f50ce2F6045d35558A5E2D8d4b2aC6610c7",
    "0xbad457dc633bbb7b6cbe09dd5867a5e8e597acd7"
]

# Ключевые слова геополитики
KEYWORDS = [
    "Trump", "Biden", "Russia", "Ukraine", "China", "war", "election",
    "international", "us-foreign-policy", "ukraine-war", "middle-east",
    "red-sea", "houthi", "taiwan", "eu-politics", "uk-politics",
    "us-congress", "white-house", "administration", "federal-reserve",
    "interest-rates", "supreme-court", "trade-wars", "crypto-policy",
    "sanctions", "energy-policy"
]

# История
seen_trades = set()
market_last_signal = {}
wallet_activity = defaultdict(list)
market_prices = defaultdict(list)

# Тестовые рынки для генерации
TEST_MARKETS = ["Russia-Ukraine conflict", "US elections 2024", "China-Taiwan tension"]

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        res = requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=10)
        if res.status_code != 200:
            print("Ошибка Telegram:", res.text)
    except Exception as e:
        print("Ошибка отправки:", e)

def contains_keyword(text):
    if not text:
        return False
    text = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text:
            return True
    return False

def check_price_anomaly(market, price):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=10)
    market_prices[market].append((price, now))
    market_prices[market] = [(p, t) for p, t in market_prices[market] if t >= cutoff]
    if not market_prices[market]:
        return None
    old_price = market_prices[market][0][0]
    if old_price == 0:
        return None
    change_pct = (price - old_price) / old_price * 100
    if abs(change_pct) >= 5:
        return round(change_pct, 2)
    return None

def calc_market_prob(market):
    last_prices = [p for p, t in market_prices[market][-N_PROB:]]
    if not last_prices:
        return None
    avg = sum(last_prices) / len(last_prices)
    return round(avg * 100, 2)

def generate_trend(market):
    last_prices = [p for p, t in market_prices[market][-N_PROB:]]
    if len(last_prices) < 2:
        return ""
    trend = ""
    for i in range(1, len(last_prices)):
        diff = last_prices[i] - last_prices[i-1]
        if diff > 0.01:
            trend += "↑"
        elif diff < -0.01:
            trend += "↓"
        else:
            trend += "→"
    return trend

def send_top_wallets():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=HOURS_ACTIVITY)
    sums = {}
    for wallet, trades in wallet_activity.items():
        total = sum(s for s, t in trades if t >= cutoff)
        if total > 0:
            sums[wallet] = total
    if not sums:
        return
    top_wallets = sorted(sums.items(), key=lambda x: x[1], reverse=True)[:5]
    text = "📊 Топ активных кошельков за последний час:\n"
    for wallet, total in top_wallets:
        text += f"👛 {wallet} — ${total}\n"
    send_message(text)

def generate_fake_trade():
    trade_id = str(random.randint(1000000, 9999999))
    trader = random.choice(WATCH_WALLETS)
    market = random.choice(TEST_MARKETS)
    size = random.randint(500, 5000)
    price = round(random.uniform(0.1, 1.0), 2)
    return {"id": trade_id, "trader": trader, "market": market, "size": size, "price": price}

def main():
    print("Тестовый бот запущен...")
    last_top = datetime.now(timezone.utc) - timedelta(minutes=TOP_INTERVAL_MIN)
    while True:
        trades = [generate_fake_trade()]
        now = datetime.now(timezone.utc)
        print(f"Сгенерировано сделок: {len(trades)}")

        for t in trades:
            trade_id = t.get("id")
            trader = t.get("trader")
            market = t.get("market")
            size = t.get("size")
            price = t.get("price")

            if trade_id in seen_trades:
                continue
            if trader not in WATCH_WALLETS:
                continue
            if size < MIN_SIZE:
                continue
            if not contains_keyword(market):
                continue

            last_signal = market_last_signal.get(market)
            if last_signal and now - last_signal < timedelta(minutes=15):
                continue
            market_last_signal[market] = now
            seen_trades.add(trade_id)

            wallet_activity[trader].append((size, now))
            last_three = [s for s, t in wallet_activity[trader][-3:]]
            anomaly = ""
            if len(last_three) >= 3 and all(s >= MIN_SIZE for s in last_three):
                anomaly = "⚡ КИТОВСКАЯ АКТИВНОСТЬ!"

            price_change = check_price_anomaly(market, price)
            price_alert = f"⚠️ Цена изменилась на {price_change}%!" if price_change else ""
            prob = calc_market_prob(market)
            prob_text = f"🔮 Системная вероятность исхода: {prob}%" if prob else ""
            trend_text = generate_trend(market)
            if trend_text:
                trend_text = f"📈 Тренд: {trend_text}"

            text = f"""
🔥 ТЕСТОВАЯ СДЕЛКА

👛 Трейдер: {trader}
📊 Событие: {market}
💰 Сумма: ${size}
📈 Цена: {price}
{anomaly}
{price_alert}
{prob_text}
{trend_text}

💡 Активность кошелька за последние 3 сделки: {sum(last_three)}

🔗 https://polymarket.com/market/{market.replace(' ', '-')}
"""
            send_message(text)

        if now - last_top >= timedelta(minutes=TOP_INTERVAL_MIN):
            send_top_wallets()
            last_top = now

        time.sleep(10)

if __name__ == "__main__":
    main()

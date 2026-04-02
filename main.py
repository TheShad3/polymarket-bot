import requests
import time
from datetime import datetime, timedelta, timezone
from telegram import Bot
import os

# -------------------------------
# Настройки Telegram из переменных окружения
# -------------------------------
TOKEN = os.getenv("TG_BOT_TOKEN")  # Добавьте токен через Variables в Railway
CHAT_ID = int(os.getenv("TG_CHAT_ID"))  # Добавьте chat_id через Variables в Railway
bot = Bot(token=TOKEN)

# -------------------------------
# Ключевые слова
# -------------------------------
KEYWORDS = [
    "Trump", "Biden", "Russia", "Ukraine", "China", "war", "election",
    "international", "us-foreign-policy", "ukraine-war", "middle-east",
    "red-sea", "houthi", "taiwan", "eu-politics", "uk-politics",
    "us-congress", "white-house", "administration", "federal-reserve",
    "interest-rates", "supreme-court", "trade-wars", "crypto-policy",
    "sanctions", "energy-policy"
]

# -------------------------------
# Кошельки для отслеживания
# -------------------------------
WATCH_WALLETS = [
    "0x7f3c8979d0afa00007bae4747d5347122af05613",
    "0xd5ccdf772f795547e299de57f47966e24de8dea4",
    "0xc2e7800b5af46e6093872b177b7a5e7f0563be51",
    "0x019782cab5d844f02bafb71f512758be78579f3c",
    "0x07b8e44b90cc3e91b8d5fe60ea810d2534638e25",
    "0xFc2F4f50ce2F6045d35558A5E2D8d4b2aC6610c7",
    "0xbad457dc633bbb7b6cbe09dd5867a5e8e597acd7"
]

LEADERBOARD_URL = "https://data-api.polymarket.com/v1/leaderboard"
CLOB_URL = "https://clob.polymarket.com/trades?limit=100"

# -------------------------------
# Пороговые параметры
# -------------------------------
MIN_AMOUNT = 100
MIN_WIN_RATE = 0.6
MIN_ACTIVE_WALLETS = 2
ANOMALY_THRESHOLD = 0.2
TOP_INTERVAL_MIN = 5  # интервал сбора топ сигналов

wallet_stats = {}
top_signals = []

# -------------------------------
# Функции
# -------------------------------
def update_watch_wallets(limit=30):
    try:
        res = requests.get(f"{LEADERBOARD_URL}?limit={limit}")
        data = res.json()
        wallets = [e.get("proxyWallet") for e in data if e.get("proxyWallet")]
        print(f"[{datetime.now(timezone.utc)}] Обновлено кошельков: {len(wallets)}")
        return wallets
    except Exception as e:
        print("Ошибка обновления кошельков:", e)
        return []

def get_recent_trades(limit=100):
    try:
        res = requests.get(CLOB_URL)
        trades = res.json()
        return trades
    except Exception as e:
        print("Ошибка загрузки сделок:", e)
        return []

def update_wallet_stats(trades):
    global wallet_stats
    for t in trades:
        if isinstance(t, dict):
            wallet = t.get("maker")
            outcome = t.get("outcome")
            amount = float(t.get("size",0))
            if wallet not in wallet_stats:
                wallet_stats[wallet] = {"wins":0, "total":0}
            if amount >= MIN_AMOUNT:
                wallet_stats[wallet]["total"] +=1
                if outcome:
                    wallet_stats[wallet]["wins"] +=1

def check_trades():
    global top_signals
    trades = get_recent_trades()
    update_wallet_stats(trades)
    market_map = {}
    
    for t in trades:
        if isinstance(t, dict):
            market_id = t.get("market", {}).get("id")
            if not market_id:
                continue
            wallet = t.get("maker")
            amount = float(t.get("size",0))
            title = t.get("market", {}).get("title","")
            probability = float(t.get("market", {}).get("probability",0))
            outcome_side = t.get("outcomeSide")
            
            win_rate = wallet_stats.get(wallet, {}).get("wins",0) / max(wallet_stats.get(wallet, {}).get("total",1),1)
            
            if (wallet in WATCH_WALLETS and
                any(k.lower() in title.lower() for k in KEYWORDS) and
                amount >= MIN_AMOUNT and
                win_rate >= MIN_WIN_RATE):
                if market_id not in market_map:
                    market_map[market_id] = []
                market_map[market_id].append({
                    "wallet": wallet,
                    "amount": amount,
                    "title": title,
                    "url": f"https://polymarket.com/market/{market_id}",
                    "win_rate": win_rate,
                    "probability": probability,
                    "outcome_side": outcome_side
                })
    
    # Сильные сигналы и аномалии
    signals_sent = 0
    for m, entries in market_map.items():
        if len(entries) >= MIN_ACTIVE_WALLETS:
            top_signals.extend(entries)
            message = f"🟢 *Сильный сигнал:* {entries[0]['title']}\n\n"
            for e in entries:
                message += f"Кошелек: {e['wallet']}\nСумма: ${e['amount']}\nWinRate: {e['win_rate']*100:.1f}%\nСсылка: [Открыть]({e['url']})\n\n"
            bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
            signals_sent += 1
        
        for e in entries:
            if e["outcome_side"]=="YES" and e["probability"] < 0.5 - ANOMALY_THRESHOLD:
                bot.send_message(chat_id=CHAT_ID,
                    text=f"⚠️ *Аномалия:* {e['title']}\nКошелек {e['wallet']} ставит YES против вероятности {e['probability']*100:.1f}%\nСумма: ${e['amount']}\n[Открыть]({e['url']})",
                    parse_mode="Markdown")
            elif e["outcome_side"]=="NO" and e["probability"] > 0.5 + ANOMALY_THRESHOLD:
                bot.send_message(chat_id=CHAT_ID,
                    text=f"⚠️ *Аномалия:* {e['title']}\nКошелек {e['wallet']} ставит NO против вероятности {e['probability']*100:.1f}%\nСумма: ${e['amount']}\n[Открыть]({e['url']})",
                    parse_mode="Markdown")
    print(f"[{datetime.now(timezone.utc)}] Проверено {len(trades)} сделок, отправлено сигналов: {signals_sent}")

def send_top_signals():
    global top_signals
    if not top_signals:
        return
    sorted_signals = sorted(top_signals, key=lambda x: x["amount"]*x["win_rate"], reverse=True)
    message = "🏆 *ТОП сигналы за последние минуты:*\n\n"
    for e in sorted_signals[:10]:
        emoji = "🟢" if e["win_rate"] >= 0.6 else "⚠️"
        message += (
            f"{emoji} *{e['title']}*\n"
            f"💰 Сумма: ${e['amount']}\n"
            f"📈 WinRate: {e['win_rate']*100:.1f}%\n"
            f"🔗 [Ссылка]({e['url']})\n"
            f"⏱ {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}\n\n"
        )
    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
    top_signals = []

def main():
    last_wallet_update = datetime.now(timezone.utc) - timedelta(minutes=61)
    last_top_send = datetime.now(timezone.utc) - timedelta(minutes=TOP_INTERVAL_MIN)
    
    while True:
        now = datetime.now(timezone.utc)
        if (now - last_wallet_update) >= timedelta(minutes=60):
            new_wallets = update_watch_wallets(30)
            if new_wallets:
                WATCH_WALLETS.clear()
                WATCH_WALLETS.extend(new_wallets)
            last_wallet_update = now
        
        check_trades()
        
        if (now - last_top_send) >= timedelta(minutes=TOP_INTERVAL_MIN):
            send_top_signals()
            last_top_send = now
        
        time.sleep(10)

if __name__ == "__main__":
    print("Бот запущен...")
    main()

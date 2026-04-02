import os
import time
import requests
from telegram import Bot
from datetime import datetime, timedelta

# ----------------------------
# Переменные окружения
# ----------------------------
TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("Переменные окружения TG_BOT_TOKEN и TG_CHAT_ID должны быть установлены!")

CHAT_ID = int(CHAT_ID)
bot = Bot(token=TOKEN)

# ----------------------------
# Настройки фильтров
# ----------------------------
MIN_AMOUNT = 50  # минимальная сумма сделки
MIN_WIN_RATE = 0.5  # минимальный win rate кошелька
TOP_INTERVAL_MIN = 10  # интервал для анализа топовых кошельков

# ----------------------------
# Ключевые слова для геополитики
# ----------------------------
KEYWORDS = [
    "Trump", "Biden", "Russia", "Ukraine", "China", "war", "election", "international",
    "us-foreign-policy", "ukraine-war", "middle-east", "red-sea", "houthi", "taiwan",
    "eu-politics", "uk-politics", "us-congress", "white-house", "administration",
    "federal-reserve", "interest-rates", "supreme-court", "trade-wars", "crypto-policy",
    "sanctions", "energy-policy"
]

# ----------------------------
# Список кошельков для отслеживания
# ----------------------------
WATCH_WALLETS = [
    # Старые кошельки
    "0x7f3c8979d0afa00007bae4747d5347122af05613",
    "0xd5ccdf772f795547e299de57f47966e24de8dea4",
    "0xc2e7800b5af46e6093872b177b7a5e7f0563be51",
    "0x019782cab5d844f02bafb71f512758be78579f3c",
    "0x07b8e44b90cc3e91b8d5fe60ea810d2534638e25",
    "0xFc2F4f50ce2F6045d35558A5E2D8d4b2aC6610c7",
    "0xbad457dc633bbb7b6cbe09dd5867a5e8e597acd7",

    # Новые топ-кошельки
    "0x6a72...33ee",
    "0x4f8a...92bc",
    "0xb3c1...5d44",
    "0x7e29...a16f",
    "0xd94e...2281",
    "0x8b21...f74a",
    "0x3f4d...c912",
    "0x1a9d...e83b",
    "0x5c38...9b0d",
    "0xf71c...3a20",
    "0x2e84...7f91",
    "0x492442EaB586F242B53bDa933fD5e859c8A3782",
    "0x0222...8ff7",
    "0xee61...debf",
    "0xb45a...192c",
    "0xdc87...7ab6",
    "0x204f...5e14",
    "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
    "0x1234567890abcdef1234567890abcdef12345678",
    "0x90abcdef1234567890abcdef1234567890abcdef",
    "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    "0xbeadfeedbeadfeedbeadfeedbeadfeedbeadfeed",
    "0xfeedfacefeedfacefeedfacefeedfacefeedface",
    "0xcafebabecafebabecafebabecafebabecafebabe",
    "0xfaceb00cfaceb00cfaceb00cfaceb00cfaceb00c"
]

# ----------------------------
# Основная функция бота
# ----------------------------
def fetch_trades():
    url = "https://api.thegraph.com/subgraphs/name/protofire/polymarket"
    query = """
    {
      trades(first: 20, orderBy: timestamp, orderDirection: desc) {
        id
        market {
          id
          title
        }
        amount
        outcome
        trader {
          id
          totalTrades
          winRate
        }
        timestamp
      }
    }
    """
    try:
        response = requests.post(url, json={"query": query}, timeout=10)
        data = response.json()
        return data["data"]["trades"]
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return []

def main():
    print("Бот запущен...")
    last_top = datetime.utcnow() - timedelta(minutes=TOP_INTERVAL_MIN)

    while True:
        trades = fetch_trades()
        print(f"Получено сделок: {len(trades)}")

        signals_sent = 0

        for t in trades:
            # Проверяем тип данных
            if isinstance(t, dict):
                trade_id = t.get("id")
                trader = t.get("trader", {})
                wallet = trader.get("id")
                win_rate = trader.get("winRate", 0)
                total_trades = trader.get("totalTrades", 0)
                market = t.get("market", {})
                title = market.get("title", "")
                amount = float(t.get("amount", 0))

                if (
                    wallet in WATCH_WALLETS
                    and amount >= MIN_AMOUNT
                    and win_rate >= MIN_WIN_RATE
                    and any(k.lower() in title.lower() for k in KEYWORDS)
                ):
                    msg = f"Сигнал от кошелька: {wallet}\nСделка: {title}\nСумма: {amount}\nWin rate: {win_rate}\nСсылка на лот: https://polymarket.com/market/{market.get('id')}"
                    bot.send_message(chat_id=CHAT_ID, text=msg)
                    signals_sent += 1

        print(f"Проверено {len(trades)} сделок, отправлено сигналов: {signals_sent}")
        time.sleep(15)  # проверка каждые 15 секунд

if __name__ == "__main__":
    main()

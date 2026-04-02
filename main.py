import requests
import time
import os
from telegram import Bot

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)
seen_trades = set()

GRAPH_URL = "https://api.thegraph.com/subgraphs/name/protofire/polymarket"

def fetch_trades():
    query = """
    {
      trades(first: 10, orderBy: timestamp, orderDirection: desc) {
        id
        trader
        market {
          question
        }
        price
        size
      }
    }
    """

    try:
        res = requests.post(GRAPH_URL, json={"query": query}, timeout=10)
        data = res.json()
        trades = data.get("data", {}).get("trades", [])

        print(f"Получено: {len(trades)}")
        return trades

    except Exception as e:
        print("Ошибка:", e)
        return []

def send_signal(trade):
    text = f"""
🔥 СДЕЛКА

👛 {trade.get('trader')}
📊 {trade.get('market', {}).get('question')}
💰 {trade.get('size')}
📈 {trade.get('price')}
"""

    bot.send_message(chat_id=CHAT_ID, text=text)

def main():
    print("Бот запущен...")

    while True:
        trades = fetch_trades()

        for t in trades:
            if t["id"] not in seen_trades:
                send_signal(t)
                seen_trades.add(t["id"])

        time.sleep(10)

if __name__ == "__main__":
    main()

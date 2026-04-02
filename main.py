import requests
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

seen_trades = set()

GRAPH_URL = "https://api.thegraph.com/subgraphs/name/protofire/polymarket"

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text
    })

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
        return data.get("data", {}).get("trades", [])
    except Exception as e:
        print("Ошибка:", e)
        return []

def main():
    print("Бот запущен...")

    while True:
        trades = fetch_trades()

        for t in trades:
            if t["id"] not in seen_trades:
                text = f"""
🔥 СДЕЛКА

👛 {t.get('trader')}
📊 {t.get('market', {}).get('question')}
💰 {t.get('size')}
📈 {t.get('price')}
"""
                send_message(text)
                seen_trades.add(t["id"])

        time.sleep(10)

if __name__ == "__main__":
    main()

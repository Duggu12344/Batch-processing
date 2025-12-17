import requests
import json
import os
from datetime import datetime

def fetch_prices(crypto_ids, currency="usd"):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(crypto_ids),
        "vs_currencies": currency
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def read_json(filename):
    if not os.path.exists(filename):
        return []

    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def update_json_batch(prices, filename="crypto_price.json"):
    data = read_json(filename)
    print(data)
    timestamp = datetime.utcnow().isoformat() + "Z"

    for crypto, value in prices.items():
        data.append({
            "timestamp": timestamp,
            "crypto": crypto,
            "price_usd": value["usd"]
        })

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
if __name__ == "__main__":
    cryptos = ["bitcoin", "ethereum", "solana"]

    prices = fetch_prices(cryptos)
    update_json_batch(prices)

    print("JSON batch update completed.")

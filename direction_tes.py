import time
import requests

COINS = {
    "BTC": "BTC-USD",
    "XRP": "XRP-USD",
    "DOGE": "DOGE-USD",
    "SOL": "SOL-USD",
}


def get_price(product: str) -> float:
    url = f"https://api.exchange.coinbase.com/products/{product}/ticker"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return float(response.json()["price"])


print("Leyendo precios iniciales...\n")

initial_prices = {}

for symbol, product in COINS.items():
    initial_prices[symbol] = get_price(product)
    print(f"{symbol} inicial: ${initial_prices[symbol]:,.6f}")

print("\nEsperando 10 segundos...\n")
time.sleep(10)

for symbol, product in COINS.items():
    current_price = get_price(product)
    previous_price = initial_prices[symbol]

    if current_price > previous_price:
        direction = "SUBIENDO"
    elif current_price < previous_price:
        direction = "BAJANDO"
    else:
        direction = "IGUAL"

    print(
        f"{symbol}: ${previous_price:,.6f} → "
        f"${current_price:,.6f} | {direction}"
    )
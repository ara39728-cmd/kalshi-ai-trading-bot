import re
import time
from datetime import datetime, timezone
from typing import Any

import requests

BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

COINS = {
    "BTC": {
        "coinbase": "BTC-USD",
        "patterns": (r"\bBTC\b", r"\bBITCOIN\b"),
    },
    "XRP": {
        "coinbase": "XRP-USD",
        "patterns": (r"\bXRP\b", r"\bRIPPLE\b"),
    },
    "DOGE": {
        "coinbase": "DOGE-USD",
        "patterns": (r"\bDOGE\b", r"\bDOGECOIN\b"),
    },
    "SOL": {
        "coinbase": "SOL-USD",
        "patterns": (r"\bSOLANA\b",),
    },
}

session = requests.Session()
session.headers.update({"User-Agent": "aramis-kalshi-scanner/1.0"})


def get_json(
    url: str,
    params: dict[str, Any] | None = None,
    attempts: int = 5,
) -> dict[str, Any]:
    delay = 2

    for attempt in range(1, attempts + 1):
        response = session.get(url, params=params, timeout=20)

        if response.status_code == 429:
            print(
                f"Kalshi pidió esperar. Intento {attempt}/{attempts}; "
                f"esperando {delay} segundos..."
            )
            time.sleep(delay)
            delay *= 2
            continue

        response.raise_for_status()
        return response.json()

    raise RuntimeError("Kalshi sigue limitando las solicitudes.")


def get_coinbase_price(product: str) -> float:
    data = get_json(
        f"https://api.exchange.coinbase.com/products/{product}/ticker"
    )
    return float(data["price"])


def get_crypto_series() -> list[dict[str, Any]]:
    data = get_json(
        f"{BASE_URL}/series",
        params={"category": "Crypto"},
    )
    return data.get("series", [])


def series_text(series: dict[str, Any]) -> str:
    tags = series.get("tags", []) or []

    return " ".join(
        [
            str(series.get("ticker", "")),
            str(series.get("title", "")),
            str(series.get("frequency", "")),
            " ".join(str(tag) for tag in tags),
        ]
    ).upper()


def matches_symbol(
    series: dict[str, Any],
    patterns: tuple[str, ...],
) -> bool:
    text = series_text(series)
    return any(re.search(pattern, text) for pattern in patterns)


def score_series(series: dict[str, Any]) -> int:
    title = str(series.get("title", "")).lower()
    frequency = str(series.get("frequency", "")).lower()
    ticker = str(series.get("ticker", "")).upper()

    score = 0

    if "price" in title:
        score += 10
    if "above" in title or "below" in title:
        score += 4
    if "range" in title:
        score += 4
    if frequency == "hourly":
        score += 8
    elif frequency == "daily":
        score += 4

    unwanted_words = (
        "flip",
        "nasdaq",
        "market cap",
        "dominance",
        "ratio",
        "maximum",
        "minimum",
        "monthly",
        "year",
    )

    if any(word in title for word in unwanted_words):
        score -= 20

    if ticker.endswith("E") or "PRICE" in ticker:
        score += 3

    return score


def choose_candidate_series(
    series_list: list[dict[str, Any]],
    patterns: tuple[str, ...],
) -> list[dict[str, Any]]:
    matches = [
        series
        for series in series_list
        if matches_symbol(series, patterns)
    ]

    matches.sort(key=score_series, reverse=True)

    # Solo revisa las tres mejores para evitar demasiadas llamadas.
    return matches[:3]


def get_open_markets(series_ticker: str) -> list[dict[str, Any]]:
    data = get_json(
        f"{BASE_URL}/markets",
        params={
            "series_ticker": series_ticker,
            "status": "open",
            "limit": 100,
            "mve_filter": "exclude",
        },
    )
    return data.get("markets", [])


def price_number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def close_timestamp(market: dict[str, Any]) -> float:
    raw = market.get("close_time") or market.get("expected_expiration_time")

    if not raw:
        return float("inf")

    try:
        normalized = str(raw).replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return float("inf")


def market_is_tradeable(market: dict[str, Any]) -> bool:
    yes_bid = price_number(market.get("yes_bid_dollars"))
    yes_ask = price_number(market.get("yes_ask_dollars"))

    return yes_bid > 0 or yes_ask > 0


def choose_best_market(
    markets: list[dict[str, Any]],
) -> dict[str, Any] | None:
    tradeable = [market for market in markets if market_is_tradeable(market)]

    if not tradeable:
        return None

    now = datetime.now(timezone.utc).timestamp()

    future_markets = [
        market
        for market in tradeable
        if close_timestamp(market) > now
    ]

    candidates = future_markets or tradeable
    candidates.sort(key=close_timestamp)

    return candidates[0]


def show_selected_market(
    symbol: str,
    coinbase_price: float,
    series: dict[str, Any],
    market: dict[str, Any],
) -> None:
    print("=" * 65)
    print(f"{symbol} Coinbase: ${coinbase_price:,.6f}")
    print(f"Serie: {series.get('ticker', 'N/D')}")
    print(f"Título de serie: {series.get('title', 'N/D')}")
    print(f"Contrato elegido: {market.get('ticker', 'N/D')}")
    print(f"Mercado: {market.get('title', 'N/D')}")
    print(f"Cierre: {market.get('close_time', 'N/D')}")
    print(f"Comprar YES: ${market.get('yes_ask_dollars', 'N/D')}")
    print(f"Vender YES: ${market.get('yes_bid_dollars', 'N/D')}")
    print(f"Último precio: ${market.get('last_price_dollars', 'N/D')}")
    print()


def main() -> None:
    print("ESCÁNER COINBASE + KALSHI")
    print("MODO SEGURO: solo lectura; no compra ni vende.\n")

    try:
        series_list = get_crypto_series()
        print(f"Series Crypto descargadas: {len(series_list)}\n")

        for symbol, config in COINS.items():
            coinbase_price = get_coinbase_price(config["coinbase"])
previous_price = coinbase_price
time.sleep(10)
current_price = get_coinbase_price(config["coinbase"])

if current_price > previous_price:
    direction = "SUBIENDO"
elif current_price < previous_price:
    direction = "BAJANDO"
else:
    direction = "IGUAL"
candidate_series = choose_candidate_series(         
                series_list,
                config["patterns"],
            )

selected_series = None
selected_market = None

for series in candidate_series:
                ticker = str(series.get("ticker", ""))

if not ticker:
continue

markets = get_open_markets(ticker)
market = choose_best_market(markets)

if market is not None:
                    selected_series = series
                    selected_market = market
                    break

                time.sleep(1)

            if selected_series is None or selected_market is None:
                print("=" * 65)
                print(f"{symbol} Coinbase: ${coinbase_price:,.6f}")
                print("Kalshi: no encontré un contrato activo con precio.")
                print()
            else:
                show_selected_market(
                    symbol,
                    coinbase_price,
                    selected_series,
                    selected_market,
                )

            time.sleep(2)

    except requests.RequestException as error:
        print(f"ERROR de conexión/API: {error}")
    except Exception as error:
        print(f"ERROR: {error}")


if __name__ == "__main__":
    main()
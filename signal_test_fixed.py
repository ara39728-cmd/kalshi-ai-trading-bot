import time
from typing import Any

from simple_kalshi_bot import (
    COINS,
    choose_best_market,
    choose_candidate_series,
    get_coinbase_price,
    get_crypto_series,
    get_open_markets,
)

MAX_PER_TRADE = 5.00


def coinbase_direction(product: str) -> tuple[float, float, str]:
    first_price = get_coinbase_price(product)
    time.sleep(10)
    second_price = get_coinbase_price(product)

    if second_price > first_price:
        direction = "SUBIENDO"
    elif second_price < first_price:
        direction = "BAJANDO"
    else:
        direction = "IGUAL"

    return first_price, second_price, direction


def kalshi_yes_direction(market: dict[str, Any]) -> str:
    text = (
        f"{market.get('title', '')} "
        f"{market.get('subtitle', '')}"
    ).lower()

    bullish_words = (" up ", "above", "higher", "increase")
    bearish_words = (" down ", "below", "lower", "decrease")

    padded_text = f" {text} "

    if any(word in padded_text for word in bullish_words):
        return "SUBIENDO"

    if any(word in padded_text for word in bearish_words):
        return "BAJANDO"

    return "DESCONOCIDA"


def parse_price(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def simulate_yes_order(market: dict[str, Any]) -> None:
    yes_ask = parse_price(market.get("yes_ask_dollars"))

    if yes_ask <= 0 or yes_ask > 1:
        print("SIMULACIÓN: no se puede calcular la orden; precio YES inválido.")
        return

    contracts = int(MAX_PER_TRADE // yes_ask)

    if contracts <= 0:
        print("SIMULACIÓN: $5 no alcanzan para un contrato.")
        return

    estimated_cost = contracts * yes_ask

    print("🟢 SEÑAL VÁLIDA: el bot prepararía una compra YES.")
    print(f"Precio YES: ${yes_ask:.2f}")
    print(f"Contratos simulados: {contracts}")
    print(f"Costo estimado: ${estimated_cost:.2f}")
    print("MODO SEGURO: no se envió ninguna orden real.")


def main() -> None:
    print("PRUEBA DE SEÑALES COINBASE + KALSHI")
    print("MODO SEGURO: no compra ni vende.\n")

    series_list = get_crypto_series()

    for symbol, config in COINS.items():
        print("=" * 60)
        print(f"Analizando {symbol}...")

        first, second, coinbase_move = coinbase_direction(
            config["coinbase"]
        )

        print(f"Coinbase inicial: ${first:,.6f}")
        print(f"Coinbase final:   ${second:,.6f}")
        print(f"Dirección Coinbase: {coinbase_move}")

        candidate_series = choose_candidate_series(
            series_list,
            config["patterns"],
        )

        selected_market = None

        for series in candidate_series:
            ticker = str(series.get("ticker", ""))

            if not ticker:
                continue

            markets = get_open_markets(ticker)
            selected_market = choose_best_market(markets)

            if selected_market is not None:
                break

            time.sleep(1)

        if selected_market is None:
            print("Kalshi: no encontré contrato activo.")
            print("DECISIÓN: NO OPERAR\n")
            continue

        kalshi_move = kalshi_yes_direction(selected_market)

        print(f"Contrato: {selected_market.get('ticker', 'N/D')}")
        print(f"Mercado: {selected_market.get('title', 'N/D')}")
        print(f"Dirección YES de Kalshi: {kalshi_move}")

        if coinbase_move == "IGUAL":
            decision = "NO OPERAR"
        elif kalshi_move == "DESCONOCIDA":
            decision = "NO OPERAR"
        elif coinbase_move == kalshi_move:
            decision = "SEÑAL COINCIDENTE - COMPRAR YES"
        else:
            decision = "NO OPERAR"

        print(f"DECISIÓN: {decision}")

        if decision == "SEÑAL COINCIDENTE - COMPRAR YES":
            simulate_yes_order(selected_market)
        else:
            print("🔴 No se realiza compra.")

        print()
        time.sleep(2)


if __name__ == "__main__":
    main()

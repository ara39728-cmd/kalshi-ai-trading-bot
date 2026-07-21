MAX_PER_TRADE = 5.00
MAX_TOTAL_EXPOSURE = 20.00


def calculate_contracts(
    yes_price_dollars: float,
    current_exposure: float = 0.00,
) -> int:
    if yes_price_dollars <= 0 or yes_price_dollars > 1:
        return 0

    available_total = MAX_TOTAL_EXPOSURE - current_exposure
    allowed_amount = min(MAX_PER_TRADE, available_total)

    if allowed_amount <= 0:
        return 0

    return int(allowed_amount // yes_price_dollars)


def simulate_buy_yes(
    ticker: str,
    yes_price_dollars: float,
    signal_matches: bool,
    current_exposure: float = 0.00,
) -> None:
    print("=" * 55)
    print("SIMULACIÓN DE COMPRA YES — NO ENVÍA ORDEN REAL")

    if not signal_matches:
        print("NO OPERAR: Coinbase y Kalshi no coinciden.")
        return

    contracts = calculate_contracts(
        yes_price_dollars,
        current_exposure,
    )

    if contracts <= 0:
        print("NO OPERAR: precio inválido o límite alcanzado.")
        return

    estimated_cost = contracts * yes_price_dollars

    print(f"Contrato: {ticker}")
    print(f"Precio YES: ${yes_price_dollars:.2f}")
    print(f"Contratos: {contracts}")
    print(f"Costo estimado: ${estimated_cost:.2f}")
    print(f"Exposición anterior: ${current_exposure:.2f}")
    print(f"Exposición nueva: ${current_exposure + estimated_cost:.2f}")
    print("RESULTADO: ORDEN SIMULADA, NO REAL")


simulate_buy_yes(
    ticker="PRUEBA-XRP",
    yes_price_dollars=0.40,
    signal_matches=True,
    current_exposure=0.00,
)
# swingbot/costs.py
SPREADS = {            # conservative spread in PRICE units (round-turn applied half each side)
    "XAUUSD": 0.30, "USDJPY": 0.012, "EURUSD": 0.00008, "GBPUSD": 0.00012,
    "USDCHF": 0.00010, "USDCAD": 0.00012, "NZDUSD": 0.00012,
    # Expanded universe — conservative IC Markets-style spreads (price units)
    "XAGUSD": 0.025,   # silver
    "SPX500": 0.5,     # S&P 500
    "NAS100": 1.5,     # Nasdaq 100
    "GER40": 1.2,      # DAX
    "JPN225": 8.0,     # Nikkei 225
    "UK100": 1.2,      # FTSE 100
    "BTCUSD": 40.0,    # Bitcoin
    "ETHUSD": 3.0,     # Ethereum
}

# column names to map to the values extracted from the pdf
ENDOWUS_NUM_COL_NAMES = [
    "start_balance",
    "investment",
    "redemption",
    "gains_losses",
    "end_balance",
]

# column names to map to the values extracted from the pdf
IBKR_COL_NAMES = [
    "units",
    "unit_price_usd",
    "closing_price",
    "proceeds",
    "comm",
    "basis",
    "pnl",
    "mtm_pnl",
]

# tickers to ignore due to (reverse) stock splits or m&a
TICKERS_TO_IGNORE = ["APHA", "ACB", "CNTTQ", "HEXO", "IPOE", "UNG", "TELL"]

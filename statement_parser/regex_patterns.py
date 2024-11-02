import re

FUND_SEARCH_COMPILE = re.compile(r"(SGD Acc|EUR Acc)")
FUND_NAME_COMPILE = re.compile(r"([a-z\s\-]+)", re.IGNORECASE)
VALUE_COMPILE = re.compile(r"([0-9\s\,\.\/\-]+)")

DATE_COMPILE = re.compile(r"\d{2}\/\d{2}\/\d{4}")
TRX_TYPE_COMPILE = re.compile(r"[a-z\s]+", re.IGNORECASE)

OPEN_BAL_COMPILE = re.compile(r"(Opening\sBalance\s\.?\d+)")
CLOSE_BAL_COMPILE = re.compile(r"(Closing\sBalance\s\.?\d+)")

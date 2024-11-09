import re

# regex patterns for endowus
ENDOWUS_DATE_COMPILE = re.compile(r"(\d{1,2} \w{3} \d{4})")
ENDOWUS_VALUE_COMPILE = re.compile(r"S\$\d{1,3}(?:,\d{3})*\.\d{2}", re.IGNORECASE)

# regex patterns for fwd
FWD_FUND_SEARCH_COMPILE = re.compile(r"(SGD(H?) Acc|EUR Acc)")
FWD_FUND_NAME_COMPILE = re.compile(r"([a-z\s\-]+)", re.IGNORECASE)
FWD_VALUE_COMPILE = re.compile(r"([0-9\s\,\.\/\-]+)")

FWD_ABNORMAL_COMPILE = re.compile(
    r"(SGD\nAcc|EUR\nAcc)((SGD)?[\d\s\,\.\/\-\n]+)+(?=\n|$)"
)
FWD_DATE_COMPILE = re.compile(r"\d{2}\/\d{2}\/\d{4}")
FWD_TRX_TYPE_COMPILE = re.compile(r"[a-z\s]+", re.IGNORECASE)

FWD_OPEN_BAL_COMPILE = re.compile(r"(Opening\sBalance\s\.?\d+)")
FWD_CLOSE_BAL_COMPILE = re.compile(r"(Closing\sBalance\s\.?\d+)")

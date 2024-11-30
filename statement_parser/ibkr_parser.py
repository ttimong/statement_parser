import pandas as pd
import pdfplumber

from .utils.constants import IBKR_COL_NAMES
from .utils.regex_patterns import IBKR_DATE_COMPILE, IBKR_VALUE_COMPILE


def extract_data(filename: str) -> pd.DataFrame:
    """
    Extract USD stock trades from IBKR monthly statement

    Args:
        filename (str): file path with filename. the file should be in pdf format

    Returns:
        pd.DataFrame: dataframe with stock trades
    """
    with pdfplumber.open(filename) as pdf:
        all_pages = []
        for page in pdf.pages:
            text = page.extract_text()
            all_pages.append(text)
        all_pages_str = " ".join(all_pages)
        all_str_lst: list[str] = all_pages_str.split("\n")

    # select index between line "Stocks" and "Options"
    start_idx = end_idx = None
    for idx, line in enumerate(all_str_lst):
        if line == "Stocks":
            start_idx = idx
        elif line == "Equity and Index Options":
            end_idx = idx
        if start_idx is not None and end_idx is not None:
            break

    if start_idx is None or end_idx is None:
        raise ValueError(
            "'Stocks' or 'Equity and Index Options' not found in the statement"
        )

    relevant_str_lst = all_str_lst[start_idx:end_idx]
    trx_df = pd.DataFrame()
    for idx, line in enumerate(relevant_str_lst):
        date_match = IBKR_DATE_COMPILE.match(line)
        if date_match:
            date = date_match.group()
            values_match = IBKR_VALUE_COMPILE.match(relevant_str_lst[idx + 1])
            if values_match:
                ticker = values_match.group(1)
                values = values_match.group(2).split()
                values = [float(v.replace(",", "")) for v in values]
                value_map: dict = dict(zip(IBKR_COL_NAMES, values))
                value_map.update(
                    {
                        "holdings": ticker,
                        "create_date": date,
                        "transaction_type": (
                            "BOUGHT" if value_map["units"] > 0 else "SOLD"
                        ),
                    }
                )
                values_df = pd.DataFrame(value_map, index=[0])
                values_df = values_df[
                    [
                        "holdings",
                        "units",
                        "unit_price_usd",
                        "create_date",
                        "transaction_type",
                    ]
                ]
                trx_df = pd.concat([trx_df, values_df], ignore_index=True)
    return trx_df

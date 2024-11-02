import datetime

import pandas as pd

from .regex_patterns import (
    CLOSE_BAL_COMPILE,
    DATE_COMPILE,
    FUND_NAME_COMPILE,
    FUND_SEARCH_COMPILE,
    OPEN_BAL_COMPILE,
    TRX_TYPE_COMPILE,
    VALUE_COMPILE,
)


def _extract_trx_values(string: str) -> list[float]:
    """
    Extract transaction values from a string

    Args:
        string (str): string to extract values from

    Returns:
        list[float]: list of values extracted
    """
    raw_values = VALUE_COMPILE.findall(string)
    strip_values_str = " ".join([s.strip() for s in raw_values if len(s.strip()) > 0])
    strip_values_lst = strip_values_str.split()
    values_lst = []
    for s in strip_values_lst:
        try:
            str_v = s.replace(",", "")
            if "-" in str_v:
                v = -float(str_v.replace("-", ""))
            else:
                v = float(str_v)
        except ValueError:
            continue
        values_lst.append(v)
    return values_lst


def extract_summary(
    str_lst: list[str], start_idx: int, end_idx: int, date: datetime.date
) -> pd.DataFrame:
    """
    Extract summary of IUA or AUA account

    Args:
        str_lst (list[str]): list of strings extracted from PDF
        start_idx (int): starting index of the summary
        end_idx (int): ending index of the summary
        date (datetime.date): date of the statement

    Returns:
        pd.DataFrame: summary of the IUA or AUA account
    """
    fund_found = None
    i = 1
    summary_map = {}

    # iterating from the first instance of iua/aua line till the next iua/aua line
    while start_idx + i < end_idx:
        line = str_lst[start_idx + i]

        # searching for fund name
        if FUND_SEARCH_COMPILE.search(line):
            fund_found = True
            fund_name = FUND_NAME_COMPILE.match(line).group().strip()

            values_lst = _extract_trx_values(line)
            summary_map[fund_name] = values_lst

        i += 1

        if fund_found and not FUND_SEARCH_COMPILE.search(line):
            break

    summary_df = pd.DataFrame.from_dict(
        summary_map,
        orient="index",
        columns=[
            "units",
            "unit_price_fund_currency",
            "fund_value_fund_currency",
            "value_sgd",
        ],
    ).reset_index(names="fund_name")
    summary_df["create_date"] = date
    summary_df["report_month"] = datetime.datetime.strftime(date, "%Y-%m")

    return summary_df[
        [
            "report_month",
            "create_date",
            "fund_name",
            "units",
            "unit_price_fund_currency",
            "value_sgd",
        ]
    ]


def find_ind_fund_idx(str_lst: list[str], start_idx: int, end_idx: int) -> list[int]:
    """
    Find the starting index of individual funds

    Args:
        str_lst (list[str]): list of strings extracted from PDF
        start_idx (int): starting index of the individual funds
        end_idx (int): ending index of the individual funds

    Returns:
        list[int]: list of starting index of individual funds
    """
    ind_fund_idx = []
    for idx, line in enumerate(str_lst[start_idx:end_idx]):
        if FUND_SEARCH_COMPILE.search(line):
            ind_fund_idx.append(idx + start_idx)
    return ind_fund_idx


def extract_fund_trx(
    str_lst: list[str], idx_lst: list[int], account_type: str, date: datetime.date
) -> pd.DataFrame:
    """
    Extract fund transaction details of IUA or AUA account

    Args:
        str_lst (list[str]): list of strings extracted from PDF
        idx_lst (list[int]): list of starting indexes of each fund
        account_type (str): type of account, either IUA or AUA
        date (datetime.date): date of the statement

     Returns:
        pd.DataFrame: fund transaction details of the IUA or AUA account
    """
    fund_map = {}

    # part 1 - extract data
    # l and r refers to indexes of idx_lst, while start_idx and end_idx refers to indexes of str_lst
    l = 0
    r = l + 1
    while r < len(idx_lst):
        start_idx = idx_lst[l]
        end_idx = idx_lst[r]

        fund_name = str_lst[start_idx]
        fund_map[fund_name] = []
        for idx in range(start_idx, end_idx):
            if OPEN_BAL_COMPILE.search(str_lst[idx]):
                open_found = True

                j = 1
                line = str_lst[idx + j]
                while open_found:
                    if CLOSE_BAL_COMPILE.search(line):
                        break
                    values = _extract_trx_values(line)

                    date = DATE_COMPILE.match(line).group()
                    date = datetime.datetime.strptime(date, "%d/%m/%Y").date()
                    trx_type = TRX_TYPE_COMPILE.search(line).group().strip()

                    values.append(date)
                    values.append(trx_type)

                    fund_map[fund_name].append(values)

                    j += 1
                    line = str_lst[idx + j]
        l += 1
        r = l + 1

    # part 2 - convert to df
    fund_df = pd.DataFrame()
    for k, v in fund_map.items():
        sub_df = pd.DataFrame.from_records(
            v,
            index=[k] * len(v),
            columns=[
                "units",
                "unit_price_fund_currency",
                "fx",
                "value_sgd",
                "value_fund_currency",
                "create_date",
                "transaction_type",
            ],
        )
        fund_df = pd.concat([fund_df, sub_df])

    fund_df.reset_index(names="fund_name", inplace=True)
    fund_df["account_type"] = account_type
    fund_df["report_month"] = datetime.datetime.strftime(date, "%Y-%m")

    return fund_df[
        [
            "report_month",
            "create_date",
            "account_type",
            "fund_name",
            "transaction_type",
            "units",
            "unit_price_fund_currency",
            "value_fund_currency",
            "value_sgd",
        ]
    ]

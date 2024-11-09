import datetime
import re

import pandas as pd
import pdfplumber

from statement_parser.utils.regex_patterns import (
    FWD_ABNORMAL_COMPILE,
    FWD_CLOSE_BAL_COMPILE,
    FWD_DATE_COMPILE,
    FWD_FUND_NAME_COMPILE,
    FWD_FUND_SEARCH_COMPILE,
    FWD_OPEN_BAL_COMPILE,
    FWD_TRX_TYPE_COMPILE,
    FWD_VALUE_COMPILE,
)


def extract_page(filename: str, password: str) -> list[str]:
    """
    Extract all pages from a PDF

    Args:
        filename (str): file path and name
        password (str): password to open the PDF

    Returns:
        list[str]: list of strings extracted from the PDF
    """
    with pdfplumber.open(filename, password=password) as pdf:
        all_pages = []
        for page in pdf.pages:
            text = page.extract_text(use_text_flow=True)
            fund_name_w_newline = FWD_ABNORMAL_COMPILE.search(text)
            if fund_name_w_newline:
                start_idx, end_idx = fund_name_w_newline.span()
                # step 1 replace "\n" with " " in the fund name
                corrected_fund_name = text[start_idx:end_idx].replace("\n", " ")
                # step 2 replace "SGD123" with "123" in the fund name
                corrected_fund_name = re.sub(r"SGD(?=\d)", "", corrected_fund_name)
                text = text.replace(text[start_idx:end_idx], corrected_fund_name)
            all_pages.append(text)

    return all_pages


def extract_trx_values(string: str) -> list[float]:
    """
    Extract transaction values from a string

    Args:
        string (str): string to extract values from

    Returns:
        list[float]: list of values extracted
    """
    raw_values = FWD_VALUE_COMPILE.findall(string)
    strip_values_str = " ".join(
        [s.strip().replace(",", "") for s in raw_values if s.strip()]
    )
    strip_values_lst = strip_values_str.split()
    values_lst = []
    for s in strip_values_lst:
        try:
            v = -float(s.replace("-", "")) if "-" in s else float(s)
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
        if FWD_FUND_SEARCH_COMPILE.search(line):
            fund_found = True
            fund_name = FWD_FUND_NAME_COMPILE.match(line).group().strip()

            values_lst = extract_trx_values(line)
            summary_map[fund_name] = values_lst

        i += 1

        if fund_found and not FWD_FUND_SEARCH_COMPILE.search(line):
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
        if FWD_FUND_SEARCH_COMPILE.search(line):
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
            if FWD_OPEN_BAL_COMPILE.search(str_lst[idx]):
                open_found = True

                j = 1
                line = str_lst[idx + j]
                while open_found:
                    if FWD_CLOSE_BAL_COMPILE.search(line):
                        break
                    values = extract_trx_values(line)

                    date = FWD_DATE_COMPILE.match(line).group()
                    date = datetime.datetime.strptime(date, "%d/%m/%Y").date()
                    trx_type = FWD_TRX_TYPE_COMPILE.search(line).group().strip()

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


def extract_data(file: str, password: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extract summary and transaction data from FWD monthly statement

    Args:
        file (str): file path and name
        password (str): password to open the PDF

    Returns:
        pd.DataFrame: summary data of IUA and AUA accounts
        pd.DataFrame: transaction data of IUA and AUA accounts
    """
    # Step 1 - extract raw data from pdf and save to a list
    all_pages = extract_page(file, password)
    str_lst = "\n".join(all_pages).split("\n")

    # Step 2 - Find the stat indexes of IUA and AUA keywords
    iua_idx_lst = []
    aua_idx_lst = []
    for idx, line in enumerate(str_lst):
        if line == "Initial Units Account":
            iua_idx_lst.append(idx)
        if line == "Accumulation Units Account":
            aua_idx_lst.append(idx)
        if "Valuation" in line:
            valuation_date = FWD_DATE_COMPILE.search(line).group()
            valuation_date = datetime.datetime.strptime(
                valuation_date, "%d/%m/%Y"
            ).date()

    if iua_idx_lst:
        iua_summ_start_idx = iua_idx_lst[0]
        iua_ind_start_idx = iua_idx_lst[1]

    if aua_idx_lst:
        aua_summ_start_idx = aua_idx_lst[0]
        if len(aua_idx_lst) == 2:
            aua_ind_start_idx = aua_idx_lst[1]
        elif len(aua_idx_lst) == 1:
            aua_ind_start_idx = None
    else:
        aua_ind_start_idx = None

    # Step 3 - Extract summary data of each account (IUA / AUA)
    if iua_idx_lst:
        if aua_ind_start_idx:
            iua_ind_fund_idx_lst = find_ind_fund_idx(
                str_lst, iua_ind_start_idx, aua_ind_start_idx
            ) + [aua_ind_start_idx]
            aua_ind_fund_idx_lst = find_ind_fund_idx(
                str_lst, aua_ind_start_idx, len(str_lst)
            ) + [len(str_lst)]
        else:
            iua_ind_fund_idx_lst = find_ind_fund_idx(
                str_lst, iua_ind_start_idx, len(str_lst)
            ) + [len(str_lst)]

    summary_df = pd.DataFrame()
    if iua_idx_lst:
        if aua_idx_lst:
            iua_summary_df = extract_summary(
                str_lst, iua_summ_start_idx, aua_summ_start_idx, valuation_date
            )
            aua_summary_df = extract_summary(
                str_lst, aua_summ_start_idx, len(str_lst), valuation_date
            )
            summary_df = pd.concat([summary_df, iua_summary_df, aua_summary_df])
        else:
            iua_summary_df = extract_summary(
                str_lst, iua_summ_start_idx, len(str_lst), valuation_date
            )
            summary_df = pd.concat([summary_df, iua_summary_df])

    if summary_df.empty:
        print("Something is wrong")
    else:
        summary_df = (
            summary_df.groupby(["report_month", "create_date", "fund_name"])
            .agg(
                units=("units", "sum"),
                unit_price_fund_currency=("unit_price_fund_currency", "mean"),
                value_sgd=("value_sgd", "sum"),
            )
            .reset_index()
        )

    # Step 4 - Extract fund transaction data of each account
    trx_df = pd.DataFrame()
    if iua_ind_start_idx:
        iua_trx_df = extract_fund_trx(
            str_lst, iua_ind_fund_idx_lst, "IUA", valuation_date
        )
        trx_df = pd.concat([trx_df, iua_trx_df])

    if aua_ind_start_idx:
        aua_trx_df = extract_fund_trx(
            str_lst, aua_ind_fund_idx_lst, "AUA", valuation_date
        )
        trx_df = pd.concat([trx_df, aua_trx_df])

    return summary_df, trx_df

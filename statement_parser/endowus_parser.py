import datetime
import re

import pandas as pd
import pdfplumber

from .utils.constants import ENDOWUS_COL_NAMES, ENDOWUS_GOALS, ENDOWUS_PHRASES
from .utils.regex_patterns import ENDOWUS_DATE_COMPILE, ENDOWUS_VALUE_COMPILE


def extract_page(phrases: list[str], filename: str) -> str:
    """Extract relevant pages based on phrases into a string

    Args:
        phrases (list[str]): list of phrases to identify pages
        filename (str): file path and name

    Returns:
        str: relevant page(s)
    """
    patterns = [re.compile(re.escape(phrase), re.IGNORECASE) for phrase in phrases]
    relevant_pages = []

    with pdfplumber.open(filename) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if all(pattern.search(text) for pattern in patterns):
                relevant_pages.append(text)

    return " ".join(relevant_pages)


def extract_date(filename: str) -> datetime.date:
    """Extract month end date from filename

    Args:
        filename (str): file path and name

    Returns:
        datetime.date: month end date in yyyy-mm-dd format
    """
    dt_str = ENDOWUS_DATE_COMPILE.search(filename).group()
    dt = datetime.datetime.strptime(dt_str, "%d %b %Y").date()

    return dt


def extract_data(file: str) -> dict:
    """Parsing endowus monthly statement and extracting goals data

    Args:
        file (str): file path with filename

    Returns:
        dict: nested dictionary with endowus goals and source as keys
    """
    pages = extract_page(ENDOWUS_PHRASES, file)
    str_lst = pages.split("\n")
    final_dict = {}
    for idx, line in enumerate(str_lst):
        if line in ENDOWUS_GOALS:
            counter = 1
            source = None
            final_dict[line] = {}
            while counter:
                next_line = str_lst[idx + counter]
                if "SGD Cash" in next_line:
                    source = "SGD Cash"
                elif "SRS" in next_line:
                    source = "SRS"
                elif "CPF OA" in next_line:
                    source = "CPF OA"
                elif "Total" in next_line:
                    break
                raw_values = ENDOWUS_VALUE_COMPILE.findall(next_line)

                if raw_values:
                    cleaned_values = [
                        float(v.replace("S$", "").replace(",", "")) for v in raw_values
                    ]
                    final_dict[line][source] = dict(
                        zip(ENDOWUS_COL_NAMES, cleaned_values)
                    )
                    counter += 1
                else:
                    break
    return final_dict


def dict2df(nested_dict: dict, date: datetime.date) -> pd.DataFrame:
    """Converts nested dictionary into a dataframe.

    Args:
        nested_dict (dict): nested dictionary containing endowus goals data
        date (date): month end date of endowus statement

    Returns:
        pd.DataFrame: endowus goals raw data containing these columns:
            "create_date", "goal", "source",
            "start_balance", "investment", "redemption", "gains_losses", "end_balance"
    """
    df = pd.json_normalize(nested_dict, sep="__")
    df = df.T
    df.index = df.index.str.split("__", expand=True)
    df = df.reset_index(names=["goal", "source", "metric"])
    df_pivot = df.pivot_table(
        index=["goal", "source"], columns="metric", values=0
    ).reset_index()
    df_pivot["create_date"] = date
    df_pivot = df_pivot[
        [
            "create_date",
            "goal",
            "source",
            "start_balance",
            "investment",
            "redemption",
            "gains_losses",
            "end_balance",
        ]
    ]
    return df_pivot

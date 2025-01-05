import datetime
import re
from dataclasses import dataclass

import pandas as pd
import pdfplumber

from statement_parser.abstracts.parser import AbstractParser
from statement_parser.utils.constants import ENDOWUS_NUM_COL_NAMES
from statement_parser.utils.regex_patterns import (
    ENDOWUS_DATE_COMPILE,
    ENDOWUS_VALUE_COMPILE,
)


@dataclass
class EndowusParser(AbstractParser):
    """
    Parser for Endowus monthly statement

    Args:
        file (str): file path with file name. The file should be in pdf format
        phrases (list[str]): list of phrases to identify pages
        goals (list[str]): list of endowus goals
        sources (list[str]): list of fund sources, e.g. "SGD Cash", "SRS", "CPF OA"
    """

    file: str
    phrases: list[str]
    goals: list[str]
    sources: list[str]

    def _extract_page(self) -> str:
        """Extract relevant pages based on phrases into a string

        Returns:
            str: relevant page(s)
        """
        patterns = [
            re.compile(re.escape(phrase), re.IGNORECASE) for phrase in self.phrases
        ]
        relevant_pages = []

        with pdfplumber.open(self.file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if all(pattern.search(text) for pattern in patterns):
                    relevant_pages.append(text)

        return " ".join(relevant_pages)

    def _extract_date(self) -> datetime.date:
        """Extract month end date from filename

        Returns:
            datetime.date: month end date in yyyy-mm-dd format
        """
        # eg of filename "Endowus_Statement_2510238_1 Oct 2024_to_31 Oct 2024.pdf"
        # we want to get the last date
        dt_str = ENDOWUS_DATE_COMPILE.findall(self.file)[1]
        report_date = datetime.datetime.strptime(dt_str, "%d %b %Y").date()

        return report_date

    def _dict2df(self, nested_dict: dict, date: datetime.date) -> pd.DataFrame:
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

        mask = (df_pivot[ENDOWUS_NUM_COL_NAMES]).any(axis=1)

        return df_pivot[mask]

    def extract_data(self) -> pd.DataFrame:
        """Parsing endowus monthly statement and extracting goals data

        Returns:
            pd.DataFrame: endowus goals raw data containing these columns:
                "create_date", "goal", "source",
                "start_balance", "investment", "redemption", "gains_losses", "end_balance"
        """
        src_compile = re.compile("|".join(self.sources))

        pages = self._extract_page()
        str_lst = pages.split("\n")
        final_dict: dict = {}
        for idx, line in enumerate(str_lst):
            if line in self.goals:
                counter = 1
                source = None
                final_dict[line] = {}
                while counter:
                    next_line = str_lst[idx + counter]
                    src = src_compile.search(next_line)
                    if src:
                        source = src.group()
                    elif "Total" in next_line:
                        break
                    raw_values = ENDOWUS_VALUE_COMPILE.findall(next_line)

                    if raw_values:
                        cleaned_values = [
                            float(v.replace("S$", "").replace(",", ""))
                            for v in raw_values
                        ]
                        final_dict[line][source] = dict(
                            zip(ENDOWUS_NUM_COL_NAMES, cleaned_values)
                        )
                        counter += 1
                    else:
                        break

        data_df = self._dict2df(final_dict, self._extract_date())
        return data_df

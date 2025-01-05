from dataclasses import dataclass

import pandas as pd

from statement_parser.abstracts.parser import AbstractParser
from statement_parser.utils.constants import TICKERS_TO_IGNORE


@dataclass
class SaxoParser(AbstractParser):
    """
    Parser for Saxo trades monthly statement

    Args:
        file (str): file path with file name. The file should be in xlsx format
    """

    file: str

    def extract_data(self) -> pd.DataFrame:
        """
        Extract USD stock trades from Saxo monthly statement

        Returns:
            pd.DataFrame: dataframe with stock trades
        """
        saxo = pd.read_excel(self.file)
        sub_saxo = saxo[saxo["Product"].isin(["Etf", "Stock", "Etn"])][
            ["Trade Date", "Instrument Symbol", "Event", "Quantity", "Price"]
        ]

        sub_saxo.rename(
            columns={"Trade Date": "create_date", "Quantity": "units"}, inplace=True
        )
        sub_saxo["create_date"] = pd.to_datetime(
            sub_saxo["create_date"], format="%d-%b-%Y %H:%M:%S"
        ).dt.strftime("%Y-%m-%d")
        sub_saxo["holdings"] = sub_saxo["Instrument Symbol"].str.split(":").str[0]
        sub_saxo["transaction_type"] = sub_saxo["Event"].apply(
            lambda x: "BOUGHT" if "Buy" in x else "SOLD"
        )

        price_split = sub_saxo["Price"].str.split(" ", expand=True)
        sub_saxo["unit_price_usd"] = price_split[0].astype(float)
        sub_saxo["currency"] = price_split[1]

        sub_saxo = sub_saxo[
            (sub_saxo["currency"] == "USD")
            & (~sub_saxo["holdings"].isin(TICKERS_TO_IGNORE))
        ]
        return sub_saxo[
            ["holdings", "units", "unit_price_usd", "create_date", "transaction_type"]
        ]

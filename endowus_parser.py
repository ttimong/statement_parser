import datetime
import re

import pdfplumber


def extract_page(phrases: list[str], filename: str) -> str:
    """Extract relevant pages based on phrases into a string

    Args:
        phrases (list[str]): list of phrases to identify pages
        filename (str): file path and name

    Returns:
        str: relevant page(s)
    """

    with pdfplumber.open(filename) as pdf:
        lst = []
        for page in pdf.pages:
            text = page.extract_text()
            patterns = [
                re.compile(re.escape(phrase), re.IGNORECASE) for phrase in phrases
            ]
            if all(pattern.search(text) for pattern in patterns):
                lst.append(text)
    return " ".join(lst)


def extract_values(phrase: str, extracted_pages: str) -> list[list[float]]:
    """Extract dollar values of specific funds

    Args:
        phrase (str): phrase to identify fund
        extracted_pages (str): relevant page(s) that was extracted in `extract_page` function

    Returns:
        list[list[float]]: matrix containing monthly balances and investment amounts
    """
    matrix = []
    str_lst = extracted_pages.split("\n")
    pattern = re.compile(re.escape(phrase), re.IGNORECASE)
    for idx, s in enumerate(str_lst):
        if pattern.search(s):
            raw_values = re.findall(r"S\$\d{1,3}(?:,\d{3})*\.\d{2}", str_lst[idx + 1])
            if raw_values:
                cleaned_values = [
                    float(v.replace("S$", "").replace(",", "")) for v in raw_values
                ]
                matrix.append(cleaned_values)
    return matrix


def extract_date(filename: str) -> datetime.date:
    """Extract month end date from filename

    Args:
        filename (str): file path and name

    Returns:
        datetime.date: month end date in yyyy-mm-dd format
    """
    pattern = re.compile(r"(\d{1,2} \w{3} \d{4})")
    date_match = pattern.findall(filename)
    dt_str = date_match[1]
    dt = datetime.datetime.strptime(dt_str, "%d %b %Y").date()

    return dt

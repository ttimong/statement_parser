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
    pattern = re.compile(r"(\d{1,2} \w{3} \d{4})")
    date_match = pattern.findall(filename)
    dt_str = date_match[1]
    dt = datetime.datetime.strptime(dt_str, "%d %b %Y").date()

    return dt

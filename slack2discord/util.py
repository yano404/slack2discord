import datetime
import os
import re
from typing import Union
from urllib import request


def ts2date(ts: str, fmt: str = "%y/%m/%d %H:%M:%S") -> str:
    try:
        return datetime.datetime.fromtimestamp(float(ts)).strftime(fmt)
    except ValueError:
        return ""


REGEX_SUB_STRS = {r"\\": r"/"}


def replace(text: str):
    for regex, repl in REGEX_SUB_STRS.items():
        return re.sub(regex, repl, text)


def url_unescape(url: str):
    return re.sub(r"\\/", r"/", url)


def modify_googlecal_date(text: str):
    regex_googlecal_date = r"<!date\^\d+[^|]+\|[^>]+>"
    regex_date = r"<!date\^\d+[^|]+\|([^>]+)>"
    googlecal_date = re.findall(regex_googlecal_date, text)
    date = re.findall(regex_date, text)
    for i, x in enumerate(googlecal_date):
        text = text.replace(x, date[i])
    return text


def downloadfile(url: str, savepath: Union[os.PathLike, str]) -> None:
    request.urlretrieve(url, savepath)

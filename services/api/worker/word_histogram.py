import re

from collections import Counter


WORDS = re.compile(r"(\w[\w']*\w|\w)")


def build(string: str) -> dict[str, int]:
    return dict(Counter(WORDS.findall(string.lower())))

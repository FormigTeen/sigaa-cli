import re

def strip_parentheses_terms(value: str) -> str:
    res = re.sub(r"\s*\([^()]*\)\s*", " ", value)
    res = re.sub(r"\s{2,}", " ", res).strip()
    return res

def extract_sequence(value: str) -> int:
    m = re.search(r"\d+", value)
    return int(m.group(0)) if m else 0
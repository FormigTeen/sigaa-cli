import re


def extract_times(time_code: str) -> list[str]:
    time_codes = re.findall(r"\b(\d+)([MTN]+)(\d+)\b", time_code)
    return list(map("".join, time_codes))

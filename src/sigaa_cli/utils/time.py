from datetime import datetime, timezone

def unix_seconds_dt() -> int:
    return int(datetime.now(timezone.utc).timestamp())
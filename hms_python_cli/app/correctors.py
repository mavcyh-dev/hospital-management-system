from datetime import datetime


def correct_date(value: str):
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            dt = datetime.strptime(value, fmt).date()
            display = dt.strftime("%Y-%m-%d")
            return dt, display
        except ValueError:
            continue

    return value

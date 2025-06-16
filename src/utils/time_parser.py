import re
from datetime import datetime, timedelta, date
from typing import Tuple

DAY_MAP = {"월":0,"화":1,"수":2,"목":3,"금":4,"토":5,"일":6}

# Fixed-date national holidays applicable every year
HOLIDAYS_FIXED = {
    (1, 1): "1월1일",
    (3, 1): "삼일절",
    (5, 5): "어린이날",
    (6, 6): "현충일",
    (8, 15): "광복절",
    (10, 3): "개천절",
    (10, 9): "한글날",
    (12, 25): "기독탄신일",
}

# Year-specific holidays that do not repeat every year
HOLIDAYS_EXTRA = {
    date(2025, 5, 5): "부처님오신날",
    date(2025, 5, 6): "대체공휴일",
    date(2025, 10, 8): "대체공휴일",
}


def is_holiday(d: date) -> str | None:
    """Return the holiday name for date ``d`` if it is a public holiday."""
    names = []
    fixed = HOLIDAYS_FIXED.get((d.month, d.day))
    if fixed:
        names.append(fixed)
    extra = HOLIDAYS_EXTRA.get(d)
    if extra:
        names.append(extra)
    if names:
        return ", ".join(names)
    return None


class TimeParser:
    """Parse various Korean time expressions."""

    def __init__(self, text: str):
        self.text = text.strip()

    def parse(self, base: date | None = None) -> Tuple[date, str]:
        base = base or datetime.now().date()
        q = self.text

        if "오늘" in q:
            return base, "exact"
        if "내일" in q:
            return base + timedelta(days=1), "exact"
        if "모레" in q:
            return base + timedelta(days=2), "exact"
        if "어제" in q:
            return base - timedelta(days=1), "exact"

        m = re.search(r"(\d+)일\s*후", q)
        if m:
            return base + timedelta(days=int(m.group(1))), "exact"
        m = re.search(r"(\d+)일\s*전", q)
        if m:
            return base - timedelta(days=int(m.group(1))), "exact"

        m = re.search(r"지난\s*([월화수목금토일])요일", q)
        if m:
            target = DAY_MAP[m.group(1)]
            diff = (base.weekday() - target + 7) % 7 or 7
            return base - timedelta(days=diff), "exact"
        m = re.search(r"다음\s*주\s*([월화수목금토일])요일", q)
        if m:
            target = DAY_MAP[m.group(1)]
            diff = (target - base.weekday() + 7) % 7
            return base + timedelta(days=7 + diff), "exact"

        if "지난 주" in q:
            return base - timedelta(days=7), "exact"
        if "다음 주" in q:
            return base + timedelta(days=7), "exact"

        m = re.search(r"(20\d{2})년\s*(\d{1,2})월\s*(\d{1,2})일", q)
        if m:
            y,mn,d = map(int, m.groups())
            return date(y,mn,d), "exact"
        m = re.search(r"(\d{1,2})월\s*(\d{1,2})일", q)
        if m:
            year_match = re.search(r"(20\d{2})년", q)
            y = int(year_match.group(1)) if year_match else base.year
            mn,d = map(int, m.groups())
            return date(y,mn,d), "exact"
        m = re.search(r"(20\d{2})년\s*(\d{1,2})월", q)
        if m:
            y,mn = map(int, m.groups())
            return date(y,mn,1), "month"
        m = re.search(r"(\d{1,2})월", q)
        if m:
            mn = int(m.group(1))
            return date(base.year,mn,1), "month"
        m = re.search(r"(20\d{2})년", q)
        if m:
            y = int(m.group(1))
            return date(y,1,1), "year"

        return base, "failed"

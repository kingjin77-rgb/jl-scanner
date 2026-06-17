"""미국 시장 운영 시간 체크 (서머타임 자동 처리)"""

from datetime import datetime, date, time
from typing import Optional

import pytz


US_HOLIDAYS_2026 = {
    date(2026, 1, 1),   date(2026, 1, 19),  date(2026, 2, 16),
    date(2026, 4, 3),   date(2026, 5, 25),  date(2026, 7, 3),
    date(2026, 9, 7),   date(2026, 11, 26), date(2026, 12, 25),
}


class MarketHoursChecker:
    """NYSE/NASDAQ 시장 시간 체크"""

    def __init__(self, timezone: str = "America/New_York"):
        self.tz = pytz.timezone(timezone)
        self.market_open = time(9, 30)
        self.market_close = time(16, 0)
        self.pre_market_open = time(4, 0)
        self.after_hours_close = time(20, 0)

    def now_et(self) -> datetime:
        """현재 미국 동부 시간"""
        return datetime.now(tz=self.tz)

    def is_market_open(self) -> bool:
        """정규 장 운영 여부"""
        now = self.now_et()
        if now.weekday() >= 5:
            return False
        if now.date() in US_HOLIDAYS_2026:
            return False
        return self.market_open <= now.time() <= self.market_close

    def is_pre_market(self) -> bool:
        """프리마켓 운영 여부"""
        now = self.now_et()
        if now.weekday() >= 5:
            return False
        return self.pre_market_open <= now.time() < self.market_open

    def is_after_hours(self) -> bool:
        """애프터마켓 운영 여부"""
        now = self.now_et()
        if now.weekday() >= 5:
            return False
        return self.market_close < now.time() <= self.after_hours_close

    def is_trading_day(self, d: Optional[date] = None) -> bool:
        """거래일 여부"""
        d = d or self.now_et().date()
        return d.weekday() < 5 and d not in US_HOLIDAYS_2026

    def minutes_to_open(self) -> int:
        """장 오픈까지 남은 분"""
        now = self.now_et()
        if self.is_market_open():
            return 0
        open_dt = now.replace(hour=9, minute=30, second=0, microsecond=0)
        if now.time() > self.market_close:
            from datetime import timedelta
            open_dt += timedelta(days=1)
        diff = (open_dt - now).total_seconds()
        return max(0, int(diff / 60))

    def get_status(self) -> str:
        """시장 상태 문자열"""
        if self.is_market_open():
            return "정규장 (운영중)"
        elif self.is_pre_market():
            return "프리마켓"
        elif self.is_after_hours():
            return "애프터마켓"
        else:
            return f"마감 (오픈까지 {self.minutes_to_open()}분)"

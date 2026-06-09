"""MACD 전략: 추세 전환 포착"""

from typing import Optional

import pandas as pd

from .base import BaseStrategy, Signal, SignalType


class MACDStrategy(BaseStrategy):
    """
    MACD(이동평균수렴확산) 전략
    - MACD 선이 시그널 선을 상향 돌파: 매수
    - MACD 선이 시그널 선을 하향 돌파: 매도
    - 히스토그램 방향 확인 포함
    """

    def __init__(self, params: dict = None):
        super().__init__("MACDStrategy", params)
        self.fast = self.get_param("fast_period", 12)
        self.slow = self.get_param("slow_period", 26)
        self.signal = self.get_param("signal_period", 9)

    @staticmethod
    def _ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    def _calc_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ema_fast"] = self._ema(df["close"], self.fast)
        df["ema_slow"] = self._ema(df["close"], self.slow)
        df["macd"] = df["ema_fast"] - df["ema_slow"]
        df["signal_line"] = self._ema(df["macd"], self.signal)
        df["histogram"] = df["macd"] - df["signal_line"]
        return df

    def generate_signal(self, symbol: str, df: pd.DataFrame,
                        current_price: float) -> Optional[Signal]:
        min_rows = self.slow + self.signal + 5
        if not self._validate_df(df, min_rows=min_rows):
            return None

        df = self._calc_macd(df)
        df.dropna(inplace=True)

        if len(df) < 3:
            return None

        cur = df.iloc[-1]
        prev = df.iloc[-2]

        macd_cross_up = prev["macd"] < prev["signal_line"] and cur["macd"] > cur["signal_line"]
        macd_cross_down = prev["macd"] > prev["signal_line"] and cur["macd"] < cur["signal_line"]
        hist_increasing = cur["histogram"] > prev["histogram"]
        hist_decreasing = cur["histogram"] < prev["histogram"]
        zero_line_above = cur["macd"] > 0

        if macd_cross_up:
            strength = 0.7 + (0.3 if zero_line_above else 0.0)
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=min(strength, 1.0),
                price=current_price,
                strategy_name=self.name,
                reason=f"MACD 골든크로스 (히스토그램: {cur['histogram']:.4f})",
                metadata={
                    "macd": cur["macd"],
                    "signal_line": cur["signal_line"],
                    "histogram": cur["histogram"]
                }
            )
            self._record_signal(signal)
            return signal

        if macd_cross_down:
            strength = 0.7 + (0.3 if not zero_line_above else 0.0)
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=min(strength, 1.0),
                price=current_price,
                strategy_name=self.name,
                reason=f"MACD 데드크로스 (히스토그램: {cur['histogram']:.4f})",
                metadata={
                    "macd": cur["macd"],
                    "signal_line": cur["signal_line"],
                    "histogram": cur["histogram"]
                }
            )
            self._record_signal(signal)
            return signal

        return None

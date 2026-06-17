"""볼린저 밴드 전략: 변동성 돌파"""

from typing import Optional

import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, SignalType


class BollingerStrategy(BaseStrategy):
    """
    볼린저 밴드 전략
    - 가격이 하단 밴드 하향 돌파 후 회귀: 매수
    - 가격이 상단 밴드 상향 돌파 후 회귀: 매도
    - 밴드 수축(스퀴즈) 후 돌파 시 강한 신호
    """

    def __init__(self, params: dict = None):
        super().__init__("BollingerStrategy", params)
        self.period = self.get_param("bb_period", 20)
        self.std_dev = self.get_param("bb_std", 2.0)
        self.squeeze_threshold = self.get_param("squeeze_threshold", 0.1)

    def _calc_bollinger(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["bb_mid"] = df["close"].rolling(self.period).mean()
        bb_std = df["close"].rolling(self.period).std()
        df["bb_upper"] = df["bb_mid"] + (self.std_dev * bb_std)
        df["bb_lower"] = df["bb_mid"] - (self.std_dev * bb_std)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]
        df["bb_pct"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
        return df

    @staticmethod
    def _detect_squeeze(df: pd.DataFrame, lookback: int = 20) -> bool:
        """밴드 수축 감지"""
        if len(df) < lookback:
            return False
        recent_width = df["bb_width"].iloc[-1]
        avg_width = df["bb_width"].iloc[-lookback:].mean()
        return recent_width < avg_width * 0.7

    def generate_signal(self, symbol: str, df: pd.DataFrame,
                        current_price: float) -> Optional[Signal]:
        if not self._validate_df(df, min_rows=self.period + 10):
            return None

        df = self._calc_bollinger(df)
        df.dropna(inplace=True)

        if len(df) < 5:
            return None

        cur = df.iloc[-1]
        prev = df.iloc[-2]
        squeeze = self._detect_squeeze(df)

        # 하단 밴드 근접 → 매수 (반등 기대)
        lower_touch = prev["close"] <= prev["bb_lower"]
        lower_recovery = current_price > cur["bb_lower"]

        if lower_touch and lower_recovery:
            strength = 0.6 + (0.4 if squeeze else 0.0)
            pct_b = cur["bb_pct"]
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=min(strength, 1.0),
                price=current_price,
                strategy_name=self.name,
                reason=f"볼린저 하단 반등 (%B: {pct_b:.2f}{'  스퀴즈 돌파' if squeeze else ''})",
                metadata={
                    "bb_upper": cur["bb_upper"],
                    "bb_lower": cur["bb_lower"],
                    "bb_pct": pct_b,
                    "squeeze": squeeze
                }
            )
            self._record_signal(signal)
            return signal

        # 상단 밴드 근접 → 매도 (과매수 반전)
        upper_touch = prev["close"] >= prev["bb_upper"]
        upper_decline = current_price < cur["bb_upper"]

        if upper_touch and upper_decline:
            strength = 0.6 + (0.4 if squeeze else 0.0)
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=min(strength, 1.0),
                price=current_price,
                strategy_name=self.name,
                reason=f"볼린저 상단 반전 (%B: {cur['bb_pct']:.2f})",
                metadata={
                    "bb_upper": cur["bb_upper"],
                    "bb_lower": cur["bb_lower"],
                    "bb_pct": cur["bb_pct"],
                    "squeeze": squeeze
                }
            )
            self._record_signal(signal)
            return signal

        return None

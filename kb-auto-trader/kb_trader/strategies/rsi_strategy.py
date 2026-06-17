"""RSI 전략: 과매도/과매수 역추세"""

from typing import Optional

import pandas as pd
import numpy as np

from .base import BaseStrategy, Signal, SignalType


class RSIStrategy(BaseStrategy):
    """
    RSI(상대강도지수) 전략
    - RSI < oversold: 매수 신호 (과매도)
    - RSI > overbought: 매도 신호 (과매수)
    - 다이버전스 감지 포함
    """

    def __init__(self, params: dict = None):
        super().__init__("RSIStrategy", params)
        self.period = self.get_param("rsi_period", 14)
        self.oversold = self.get_param("oversold", 30)
        self.overbought = self.get_param("overbought", 70)
        self.exit_oversold = self.get_param("rsi_exit_oversold", 40)
        self.exit_overbought = self.get_param("rsi_exit_overbought", 60)

    @staticmethod
    def _calc_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    def generate_signal(self, symbol: str, df: pd.DataFrame,
                        current_price: float) -> Optional[Signal]:
        if not self._validate_df(df, min_rows=self.period + 10):
            return None

        df = df.copy()
        df["rsi"] = self._calc_rsi(df["close"], self.period)
        df.dropna(inplace=True)

        if len(df) < 5:
            return None

        current_rsi = df["rsi"].iloc[-1]
        prev_rsi = df["rsi"].iloc[-2]

        # 과매도 → 매수
        if current_rsi < self.oversold:
            # RSI가 상향 반전 중인지 확인
            reversal = current_rsi > prev_rsi
            strength = (self.oversold - current_rsi) / self.oversold
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=min(strength + (0.2 if reversal else 0), 1.0),
                price=current_price,
                strategy_name=self.name,
                reason=f"RSI 과매도 {current_rsi:.1f} ({'반전중' if reversal else '하락중'})",
                metadata={"rsi": current_rsi, "reversal": reversal}
            )
            self._record_signal(signal)
            return signal

        # 과매수 → 매도
        if current_rsi > self.overbought:
            reversal = current_rsi < prev_rsi
            strength = (current_rsi - self.overbought) / (100 - self.overbought)
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=min(strength + (0.2 if reversal else 0), 1.0),
                price=current_price,
                strategy_name=self.name,
                reason=f"RSI 과매수 {current_rsi:.1f} ({'반전중' if reversal else '상승중'})",
                metadata={"rsi": current_rsi, "reversal": reversal}
            )
            self._record_signal(signal)
            return signal

        # 중간 구간 탈출 신호 (포지션 보유 중 청산 타이밍)
        if self.exit_oversold < current_rsi < self.exit_overbought:
            return None

        return None

"""모멘텀 전략: 추세 추종"""

from typing import Optional

import pandas as pd

from .base import BaseStrategy, Signal, SignalType


class MomentumStrategy(BaseStrategy):
    """
    모멘텀 전략
    - 일정 기간 수익률이 임계값 이상이면 매수
    - 이동평균 상향 배열 + 거래량 증가 조건 추가
    """

    def __init__(self, params: dict = None):
        super().__init__("MomentumStrategy", params)
        self.lookback = self.get_param("lookback_days", 20)
        self.threshold = self.get_param("momentum_threshold", 0.05)
        self.vol_multiplier = self.get_param("volume_multiplier", 1.5)

    def generate_signal(self, symbol: str, df: pd.DataFrame,
                        current_price: float) -> Optional[Signal]:
        if not self._validate_df(df, min_rows=self.lookback + 10):
            return None

        df = df.copy()
        df["ma20"] = df["close"].rolling(20).mean()
        df["ma50"] = df["close"].rolling(50).mean() if len(df) >= 50 else df["close"].rolling(20).mean()
        df["vol_ma20"] = df["volume"].rolling(20).mean()

        latest = df.iloc[-1]
        prev = df.iloc[-self.lookback]

        momentum = (current_price - prev["close"]) / prev["close"]
        vol_ratio = latest["volume"] / latest["vol_ma20"] if latest["vol_ma20"] > 0 else 1.0
        ma_aligned = latest["ma20"] > latest["ma50"]
        price_above_ma20 = current_price > latest["ma20"]

        # 매수 신호
        if (momentum > self.threshold and
                vol_ratio > self.vol_multiplier and
                ma_aligned and price_above_ma20):
            strength = min(1.0, (momentum / self.threshold) * 0.5 + (vol_ratio / self.vol_multiplier) * 0.5)
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=min(strength, 1.0),
                price=current_price,
                strategy_name=self.name,
                reason=f"모멘텀 {momentum:.1%}, 거래량 {vol_ratio:.1f}x",
                metadata={"momentum": momentum, "vol_ratio": vol_ratio}
            )
            self._record_signal(signal)
            return signal

        # 매도 신호: 모멘텀 소멸
        if momentum < -self.threshold * 0.5 or (ma_aligned is False and not price_above_ma20):
            signal = Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=0.6,
                price=current_price,
                strategy_name=self.name,
                reason=f"모멘텀 소멸 {momentum:.1%}"
            )
            self._record_signal(signal)
            return signal

        return None

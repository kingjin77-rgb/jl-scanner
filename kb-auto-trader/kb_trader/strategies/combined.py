"""복합 전략: 여러 전략 신호를 결합"""

from typing import Dict, List, Optional, Tuple

import pandas as pd
from loguru import logger

from .base import BaseStrategy, Signal, SignalType


class CombinedStrategy:
    """
    다중 전략 신호 결합기
    - weighted: 가중치 기반 점수 합산
    - vote: 다수결
    - unanimous: 만장일치
    """

    def __init__(self, strategies: List[Tuple[BaseStrategy, float]],
                 combine_method: str = "weighted",
                 min_score: float = 0.6):
        self.strategies = strategies  # [(strategy, weight), ...]
        self.combine_method = combine_method
        self.min_score = min_score

        total_weight = sum(w for _, w in strategies)
        self.strategies = [(s, w / total_weight) for s, w in strategies]

    def generate_signal(self, symbol: str, df: pd.DataFrame,
                        current_price: float) -> Optional[Signal]:
        """모든 전략 신호를 수집하고 결합"""
        buy_signals: List[Tuple[Signal, float]] = []
        sell_signals: List[Tuple[Signal, float]] = []

        for strategy, weight in self.strategies:
            try:
                sig = strategy.generate_signal(symbol, df, current_price)
                if sig is None:
                    continue
                if sig.is_buy:
                    buy_signals.append((sig, weight))
                elif sig.is_sell:
                    sell_signals.append((sig, weight))
            except Exception as e:
                logger.warning("전략 [{}] 신호 생성 오류: {}", strategy.name, e)

        return self._combine(symbol, current_price, buy_signals, sell_signals)

    def _combine(self, symbol: str, price: float,
                 buy_signals: List[Tuple[Signal, float]],
                 sell_signals: List[Tuple[Signal, float]]) -> Optional[Signal]:

        if self.combine_method == "weighted":
            return self._weighted_combine(symbol, price, buy_signals, sell_signals)
        elif self.combine_method == "vote":
            return self._vote_combine(symbol, price, buy_signals, sell_signals)
        elif self.combine_method == "unanimous":
            return self._unanimous_combine(symbol, price, buy_signals, sell_signals)
        return None

    def _weighted_combine(self, symbol: str, price: float,
                           buy_signals, sell_signals) -> Optional[Signal]:
        buy_score = sum(s.strength * w for s, w in buy_signals)
        sell_score = sum(s.strength * w for s, w in sell_signals)

        if buy_score >= self.min_score and buy_score > sell_score:
            reasons = " | ".join(s.reason for s, _ in buy_signals)
            return Signal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=buy_score,
                price=price,
                strategy_name="CombinedStrategy",
                reason=f"복합 매수 ({len(buy_signals)}개 전략) | {reasons}",
                metadata={"buy_score": buy_score, "sell_score": sell_score}
            )

        if sell_score >= self.min_score and sell_score > buy_score:
            reasons = " | ".join(s.reason for s, _ in sell_signals)
            return Signal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=sell_score,
                price=price,
                strategy_name="CombinedStrategy",
                reason=f"복합 매도 ({len(sell_signals)}개 전략) | {reasons}",
                metadata={"buy_score": buy_score, "sell_score": sell_score}
            )
        return None

    def _vote_combine(self, symbol: str, price: float,
                      buy_signals, sell_signals) -> Optional[Signal]:
        total = len(self.strategies)
        if len(buy_signals) > total / 2:
            avg_strength = sum(s.strength for s, _ in buy_signals) / len(buy_signals)
            return Signal(
                symbol=symbol, signal_type=SignalType.BUY,
                strength=avg_strength, price=price,
                strategy_name="CombinedStrategy",
                reason=f"다수결 매수 ({len(buy_signals)}/{total})"
            )
        if len(sell_signals) > total / 2:
            avg_strength = sum(s.strength for s, _ in sell_signals) / len(sell_signals)
            return Signal(
                symbol=symbol, signal_type=SignalType.SELL,
                strength=avg_strength, price=price,
                strategy_name="CombinedStrategy",
                reason=f"다수결 매도 ({len(sell_signals)}/{total})"
            )
        return None

    def _unanimous_combine(self, symbol: str, price: float,
                            buy_signals, sell_signals) -> Optional[Signal]:
        total = len(self.strategies)
        if len(buy_signals) == total:
            avg_strength = sum(s.strength for s, _ in buy_signals) / total
            return Signal(
                symbol=symbol, signal_type=SignalType.BUY,
                strength=avg_strength, price=price,
                strategy_name="CombinedStrategy",
                reason="만장일치 매수"
            )
        if len(sell_signals) == total:
            avg_strength = sum(s.strength for s, _ in sell_signals) / total
            return Signal(
                symbol=symbol, signal_type=SignalType.SELL,
                strength=avg_strength, price=price,
                strategy_name="CombinedStrategy",
                reason="만장일치 매도"
            )
        return None

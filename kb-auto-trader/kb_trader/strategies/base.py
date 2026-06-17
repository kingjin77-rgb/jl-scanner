"""매매 전략 기본 클래스"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

import pandas as pd


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    symbol: str
    signal_type: SignalType
    strength: float          # 신호 강도: 0.0 ~ 1.0
    price: float
    strategy_name: str
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_buy(self) -> bool:
        return self.signal_type == SignalType.BUY

    @property
    def is_sell(self) -> bool:
        return self.signal_type == SignalType.SELL


class BaseStrategy(ABC):
    """모든 전략의 기본 클래스"""

    def __init__(self, name: str, params: Dict[str, Any] = None):
        self.name = name
        self.params = params or {}
        self._signals_history: List[Signal] = []

    @abstractmethod
    def generate_signal(self, symbol: str, df: pd.DataFrame,
                        current_price: float) -> Optional[Signal]:
        """매매 신호 생성 - 하위 클래스에서 구현"""
        pass

    def _record_signal(self, signal: Signal):
        self._signals_history.append(signal)
        if len(self._signals_history) > 1000:
            self._signals_history = self._signals_history[-500:]

    def get_param(self, key: str, default=None):
        return self.params.get(key, default)

    @staticmethod
    def _validate_df(df: pd.DataFrame, min_rows: int = 30) -> bool:
        """데이터프레임 유효성 검사"""
        return df is not None and len(df) >= min_rows and "close" in df.columns

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.params})"

from .base import BaseStrategy, Signal, SignalType
from .momentum import MomentumStrategy
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .bollinger import BollingerStrategy
from .combined import CombinedStrategy

STRATEGY_REGISTRY = {
    "MomentumStrategy": MomentumStrategy,
    "RSIStrategy": RSIStrategy,
    "MACDStrategy": MACDStrategy,
    "BollingerStrategy": BollingerStrategy,
}

__all__ = [
    "BaseStrategy", "Signal", "SignalType",
    "MomentumStrategy", "RSIStrategy", "MACDStrategy",
    "BollingerStrategy", "CombinedStrategy", "STRATEGY_REGISTRY"
]

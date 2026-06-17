"""KB증권 API 데이터 모델"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MarketType(str, Enum):
    NASDAQ = "NASD"
    NYSE = "NYSE"
    AMEX = "AMEX"
    HONG_KONG = "SEHK"
    SHANGHAI_A = "SHAA"
    SHENZHEN_A = "SZAA"
    TOKYO = "TKSE"
    HANOI = "HASE"
    HOCHIMINH = "VNSE"


class OrderSide(str, Enum):
    BUY = "02"
    SELL = "01"


class OrderType(str, Enum):
    LIMIT = "00"    # 지정가
    MARKET = "01"   # 시장가


class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class StockPrice:
    symbol: str
    market: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    prev_close: float
    volume: int
    change: float
    change_pct: float
    timestamp: datetime = field(default_factory=datetime.now)
    currency: str = "USD"

    @property
    def is_up(self) -> bool:
        return self.change >= 0


@dataclass
class OrderRequest:
    symbol: str
    market: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: float = 0.0
    stop_price: float = 0.0
    strategy_name: str = ""
    memo: str = ""


@dataclass
class OrderResponse:
    order_id: str
    symbol: str
    market: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: float
    status: OrderStatus
    submitted_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    filled_price: float = 0.0
    filled_quantity: int = 0
    commission: float = 0.0
    error_message: str = ""


@dataclass
class Position:
    symbol: str
    market: str
    quantity: int
    avg_price: float
    current_price: float
    currency: str = "USD"
    entry_date: Optional[datetime] = None
    strategy_name: str = ""
    stop_loss: float = 0.0
    take_profit: float = 0.0
    trailing_stop: float = 0.0
    highest_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_price

    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100


@dataclass
class Balance:
    total_assets: float
    cash: float
    stock_value: float
    unrealized_pnl: float
    realized_pnl: float
    currency: str = "USD"
    krw_exchange_rate: float = 1300.0
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_pnl(self) -> float:
        return self.unrealized_pnl + self.realized_pnl

    @property
    def total_assets_krw(self) -> float:
        return self.total_assets * self.krw_exchange_rate


@dataclass
class OrderHistory:
    order_id: str
    symbol: str
    market: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: float
    filled_price: float
    filled_quantity: int
    status: OrderStatus
    commission: float
    created_at: datetime
    filled_at: Optional[datetime] = None

    @property
    def pnl(self) -> float:
        if self.side == OrderSide.SELL:
            return (self.filled_price - self.price) * self.filled_quantity
        return 0.0


@dataclass
class MarketHours:
    market: str
    is_open: bool
    open_time: str
    close_time: str
    timezone: str
    next_open: Optional[datetime] = None

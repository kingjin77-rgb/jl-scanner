"""백테스트 엔진"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger

from ..strategies.base import BaseStrategy, Signal, SignalType


@dataclass
class Trade:
    symbol: str
    entry_date: datetime
    entry_price: float
    exit_date: Optional[datetime] = None
    exit_price: float = 0.0
    quantity: int = 0
    side: str = "BUY"
    commission: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    exit_reason: str = ""

    @property
    def pnl(self) -> float:
        if self.exit_price == 0:
            return 0.0
        return (self.exit_price - self.entry_price) * self.quantity - self.commission * 2

    @property
    def pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.exit_price - self.entry_price) / self.entry_price * 100

    @property
    def holding_days(self) -> int:
        if not self.exit_date:
            return 0
        return (self.exit_date - self.entry_date).days


@dataclass
class BacktestResult:
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    avg_holding_days: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)


class BacktestEngine:
    """
    벡터화 백테스트 엔진
    - 수수료/세금 포함
    - 슬리피지 모델링
    - 포지션 사이징
    - 성과 지표 계산
    """

    def __init__(self, initial_capital: float = 10_000.0,
                 commission_pct: float = 0.25,
                 tax_pct: float = 0.0,
                 slippage_pct: float = 0.05,
                 stop_loss_pct: float = 3.0,
                 take_profit_pct: float = 8.0,
                 position_size_pct: float = 10.0):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct / 100
        self.tax_pct = tax_pct / 100
        self.slippage_pct = slippage_pct / 100
        self.stop_loss_pct = stop_loss_pct / 100
        self.take_profit_pct = take_profit_pct / 100
        self.position_size_pct = position_size_pct / 100

    def run(self, data: Dict[str, pd.DataFrame],
            strategy: BaseStrategy) -> BacktestResult:
        """
        백테스트 실행
        data: {symbol: OHLCV DataFrame}
        """
        capital = self.initial_capital
        trades: List[Trade] = []
        equity: Dict[datetime, float] = {}
        open_positions: Dict[str, Trade] = {}

        all_dates = sorted(set(
            date for df in data.values()
            for date in df.index
        ))

        logger.info("백테스트 시작: {} 종목, {} 거래일",
                    len(data), len(all_dates))

        for i, current_date in enumerate(all_dates):
            day_value = capital

            # 보유 포지션 업데이트
            for symbol, trade in list(open_positions.items()):
                if symbol not in data or current_date not in data[symbol].index:
                    continue
                row = data[symbol].loc[current_date]
                current_price = row["close"]

                day_value += (current_price - trade.entry_price) * trade.quantity

                # 손절/수익실현 체크
                should_exit, reason = False, ""
                if trade.stop_loss > 0 and row["low"] <= trade.stop_loss:
                    current_price = trade.stop_loss
                    should_exit, reason = True, "stop_loss"
                elif trade.take_profit > 0 and row["high"] >= trade.take_profit:
                    current_price = trade.take_profit
                    should_exit, reason = True, "take_profit"

                if should_exit:
                    exit_price = current_price * (1 - self.slippage_pct)
                    commission = exit_price * trade.quantity * self.commission_pct
                    tax = exit_price * trade.quantity * self.tax_pct
                    trade.exit_date = current_date
                    trade.exit_price = exit_price
                    trade.exit_reason = reason
                    trade.commission = commission + tax
                    capital += exit_price * trade.quantity - commission - tax
                    capital -= trade.entry_price * trade.quantity
                    trades.append(trade)
                    del open_positions[symbol]

            # 신호 생성
            if i >= 50:
                for symbol, df in data.items():
                    if symbol in open_positions:
                        continue

                    hist = df[df.index <= current_date].tail(100)
                    if len(hist) < 30:
                        continue

                    try:
                        current_price = df.loc[current_date]["close"] if current_date in df.index else None
                        if current_price is None:
                            continue

                        signal = strategy.generate_signal(symbol, hist, current_price)
                        if signal and signal.is_buy:
                            invest = capital * self.position_size_pct
                            entry_price = current_price * (1 + self.slippage_pct)
                            quantity = int(invest / entry_price)

                            if quantity > 0 and capital >= entry_price * quantity:
                                commission = entry_price * quantity * self.commission_pct
                                capital -= entry_price * quantity + commission

                                open_positions[symbol] = Trade(
                                    symbol=symbol,
                                    entry_date=current_date,
                                    entry_price=entry_price,
                                    quantity=quantity,
                                    commission=commission,
                                    stop_loss=entry_price * (1 - self.stop_loss_pct),
                                    take_profit=entry_price * (1 + self.take_profit_pct)
                                )
                    except Exception:
                        pass

            # 마지막 날 강제 청산
            if i == len(all_dates) - 1:
                for symbol, trade in list(open_positions.items()):
                    if symbol in data and current_date in data[symbol].index:
                        exit_price = data[symbol].loc[current_date]["close"]
                        commission = exit_price * trade.quantity * self.commission_pct
                        trade.exit_date = current_date
                        trade.exit_price = exit_price
                        trade.exit_reason = "period_end"
                        capital += exit_price * trade.quantity - commission
                        capital -= trade.entry_price * trade.quantity
                        trades.append(trade)

            equity[current_date] = capital

        equity_series = pd.Series(equity)
        return self._calculate_metrics(capital, equity_series, trades)

    def _calculate_metrics(self, final_capital: float,
                            equity: pd.Series, trades: List[Trade]) -> BacktestResult:
        total_return = final_capital - self.initial_capital
        total_return_pct = total_return / self.initial_capital * 100

        # 최대 낙폭
        rolling_max = equity.cummax()
        drawdown = equity - rolling_max
        max_drawdown = drawdown.min()
        max_drawdown_pct = max_drawdown / rolling_max[drawdown.idxmin()] * 100 if len(drawdown) > 0 else 0

        # 일별 수익률
        daily_returns = equity.pct_change().dropna()
        sharpe = self._sharpe(daily_returns)
        sortino = self._sortino(daily_returns)

        completed = [t for t in trades if t.exit_price > 0]
        winners = [t for t in completed if t.pnl > 0]
        losers = [t for t in completed if t.pnl <= 0]

        win_rate = len(winners) / len(completed) * 100 if completed else 0
        avg_win = np.mean([t.pnl for t in winners]) if winners else 0
        avg_loss = np.mean([abs(t.pnl) for t in losers]) if losers else 0
        profit_factor = (sum(t.pnl for t in winners) / sum(abs(t.pnl) for t in losers)
                         if losers and sum(abs(t.pnl) for t in losers) > 0 else float("inf"))
        avg_holding = np.mean([t.holding_days for t in completed]) if completed else 0

        return BacktestResult(
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(completed),
            winning_trades=len(winners),
            losing_trades=len(losers),
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_holding_days=avg_holding,
            trades=completed,
            equity_curve=equity
        )

    @staticmethod
    def _sharpe(returns: pd.Series, risk_free: float = 0.05) -> float:
        if returns.std() == 0:
            return 0.0
        excess = returns - risk_free / 252
        return float(excess.mean() / excess.std() * np.sqrt(252))

    @staticmethod
    def _sortino(returns: pd.Series, risk_free: float = 0.05) -> float:
        excess = returns - risk_free / 252
        downside = excess[excess < 0]
        if len(downside) == 0 or downside.std() == 0:
            return float("inf")
        return float(excess.mean() / downside.std() * np.sqrt(252))

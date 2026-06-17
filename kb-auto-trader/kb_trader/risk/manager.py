"""리스크 관리 모듈"""

import math
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from loguru import logger

from ..api.models import Position, Balance, OrderSide


class RiskManager:
    """
    포트폴리오 리스크 관리
    - 포지션 사이징 (Kelly / Fixed %)
    - 손절/수익실현/트레일링 스탑
    - 일일 손실 한도
    - 포트폴리오 집중도 제한
    """

    def __init__(self, config: dict):
        self.max_portfolio_loss_pct = config.get("max_portfolio_loss_pct", 10.0)
        self.max_position_size_pct = config.get("max_position_size_pct", 15.0)
        self.min_position_size_pct = config.get("min_position_size_pct", 2.0)
        self.stop_loss_pct = config.get("stop_loss_pct", 3.0)
        self.take_profit_pct = config.get("take_profit_pct", 8.0)
        self.trailing_stop_pct = config.get("trailing_stop_pct", 2.0)
        self.daily_loss_limit_pct = config.get("daily_loss_limit_pct", 3.0)
        self.position_sizer = config.get("position_sizer", "kelly")
        self.kelly_fraction = config.get("kelly_fraction", 0.25)
        self.max_drawdown_pct = config.get("max_drawdown_pct", 15.0)
        self.max_positions = config.get("max_positions", 10)

        self._daily_pnl: float = 0.0
        self._peak_value: float = 0.0
        self._trading_halted: bool = False

    # ── 포지션 사이징 ──────────────────────────────────────────────────

    def calculate_position_size(self, total_cash: float, price: float,
                                  win_rate: float = 0.55,
                                  avg_win: float = 0.08,
                                  avg_loss: float = 0.03) -> Tuple[int, float]:
        """
        포지션 수량 계산
        Returns: (수량, 투자금액)
        """
        if self.position_sizer == "kelly":
            amount = self._kelly_position(
                total_cash, price, win_rate, avg_win, avg_loss
            )
        elif self.position_sizer == "fixed_pct":
            amount = total_cash * (self.max_position_size_pct / 100)
        else:
            amount = total_cash / self.max_positions

        amount = min(amount, total_cash * (self.max_position_size_pct / 100))
        amount = max(amount, total_cash * (self.min_position_size_pct / 100))

        quantity = int(amount / price) if price > 0 else 0
        actual_amount = quantity * price
        return quantity, actual_amount

    def _kelly_position(self, total_cash: float, price: float,
                         win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Kelly Criterion 포지션 사이징"""
        if avg_loss <= 0:
            return total_cash * 0.05

        q = 1 - win_rate
        b = avg_win / avg_loss
        kelly = (b * win_rate - q) / b

        kelly = max(0, kelly) * self.kelly_fraction
        kelly = min(kelly, self.max_position_size_pct / 100)
        return total_cash * kelly

    # ── 손절/수익실현 수준 계산 ─────────────────────────────────────────

    def calculate_exits(self, entry_price: float) -> Tuple[float, float, float]:
        """
        손절/수익실현/트레일링 스탑 가격 계산
        Returns: (stop_loss, take_profit, trailing_stop)
        """
        stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
        take_profit = entry_price * (1 + self.take_profit_pct / 100)
        trailing_stop = entry_price * (1 - self.trailing_stop_pct / 100)
        return stop_loss, take_profit, trailing_stop

    def update_trailing_stop(self, position: Position) -> float:
        """트레일링 스탑 업데이트"""
        if position.current_price > position.highest_price:
            position.highest_price = position.current_price
            new_trailing = position.highest_price * (1 - self.trailing_stop_pct / 100)
            position.trailing_stop = max(position.trailing_stop, new_trailing)
        return position.trailing_stop

    # ── 신호 검증 ─────────────────────────────────────────────────────

    def check_exit_conditions(self, position: Position) -> Tuple[bool, str]:
        """
        포지션 청산 조건 확인
        Returns: (청산 여부, 이유)
        """
        current = position.current_price

        # 손절
        if position.stop_loss > 0 and current <= position.stop_loss:
            loss_pct = position.unrealized_pnl_pct
            return True, f"손절 ({loss_pct:.1f}%)"

        # 수익실현
        if position.take_profit > 0 and current >= position.take_profit:
            gain_pct = position.unrealized_pnl_pct
            return True, f"수익실현 ({gain_pct:.1f}%)"

        # 트레일링 스탑
        trailing = self.update_trailing_stop(position)
        if trailing > 0 and current <= trailing:
            return True, f"트레일링 스탑 ({position.unrealized_pnl_pct:.1f}%)"

        return False, ""

    def can_open_position(self, balance: Balance,
                           positions: List[Position],
                           investment_amount: float) -> Tuple[bool, str]:
        """신규 포지션 오픈 가능 여부 확인"""
        if self._trading_halted:
            return False, "거래 일시 중단 (리스크 한도 초과)"

        if len(positions) >= self.max_positions:
            return False, f"최대 포지션 수 도달 ({self.max_positions})"

        if balance.cash < investment_amount:
            return False, f"현금 부족 (보유: ${balance.cash:.0f}, 필요: ${investment_amount:.0f})"

        portfolio_value = balance.total_assets
        if portfolio_value > 0:
            position_pct = (investment_amount / portfolio_value) * 100
            if position_pct > self.max_position_size_pct:
                return False, f"포지션 크기 초과 ({position_pct:.1f}% > {self.max_position_size_pct}%)"

        if self._daily_pnl < -(portfolio_value * self.daily_loss_limit_pct / 100):
            self._trading_halted = True
            return False, f"일일 손실 한도 초과 ({self._daily_pnl:.0f})"

        return True, ""

    def check_portfolio_risk(self, balance: Balance) -> Tuple[bool, str]:
        """포트폴리오 전체 리스크 체크"""
        if self._peak_value < balance.total_assets:
            self._peak_value = balance.total_assets

        if self._peak_value > 0:
            drawdown = (self._peak_value - balance.total_assets) / self._peak_value * 100
            if drawdown > self.max_drawdown_pct:
                self._trading_halted = True
                logger.critical("최대 낙폭 초과! MDD: {:.1f}% - 자동매매 중단", drawdown)
                return False, f"MDD 초과 ({drawdown:.1f}%)"

        return True, ""

    def update_daily_pnl(self, pnl: float):
        self._daily_pnl = pnl

    def reset_daily(self):
        """일일 초기화"""
        self._daily_pnl = 0.0
        self._trading_halted = False
        logger.info("일일 리스크 카운터 초기화")

    def resume_trading(self):
        """거래 재개 (수동 승인 후)"""
        self._trading_halted = False
        logger.warning("거래 재개 승인됨")

    @property
    def is_halted(self) -> bool:
        return self._trading_halted

    def get_atr_stop(self, df: pd.DataFrame, multiplier: float = 2.0) -> float:
        """ATR 기반 동적 손절선 계산"""
        if len(df) < 15:
            return 0.0
        high = df["high"].iloc[-14:]
        low = df["low"].iloc[-14:]
        close = df["close"].iloc[-15:-1]

        tr = pd.concat([
            high - low,
            (high - close.values).abs(),
            (low - close.values).abs()
        ], axis=1).max(axis=1)
        atr = tr.mean()
        return df["close"].iloc[-1] - (atr * multiplier)

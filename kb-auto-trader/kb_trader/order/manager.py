"""주문 관리 모듈"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from ..api.client import KBApiClient
from ..api.models import (
    OrderRequest, OrderResponse, OrderSide, OrderStatus,
    OrderType, Position
)
from ..strategies.base import Signal, SignalType


class OrderManager:
    """
    주문 생성, 추적, 체결 확인
    - 중복 주문 방지
    - 주문 상태 모니터링
    - 부분 체결 처리
    """

    def __init__(self, api_client: KBApiClient, config: dict,
                 db_path: str = "data/trading.db"):
        self.api = api_client
        self.market = config.get("market", "NASD")
        self.order_type = OrderType(config.get("order_type", "00"))
        self.slippage_pct = config.get("slippage_pct", 0.05)
        self._pending_orders: Dict[str, OrderResponse] = {}
        self._filled_orders: List[OrderResponse] = []
        self._order_log_path = Path("data/orders.jsonl")
        self._order_log_path.parent.mkdir(exist_ok=True)

    def execute_buy(self, signal: Signal, quantity: int,
                     stop_loss: float = 0.0, take_profit: float = 0.0) -> Optional[OrderResponse]:
        """매수 주문 실행"""
        if quantity <= 0:
            logger.warning("매수 수량이 0 이하: {}", signal.symbol)
            return None

        if self._has_pending_order(signal.symbol, OrderSide.BUY):
            logger.info("이미 매수 주문 대기 중: {}", signal.symbol)
            return None

        # 시장가 주문 시 슬리피지 포함
        price = signal.price
        if self.order_type == OrderType.MARKET:
            price = 0.0
        else:
            price = signal.price * (1 + self.slippage_pct / 100)

        order_req = OrderRequest(
            symbol=signal.symbol,
            market=self.market,
            side=OrderSide.BUY,
            order_type=self.order_type,
            quantity=quantity,
            price=round(price, 2),
            strategy_name=signal.strategy_name,
            memo=signal.reason[:50] if signal.reason else ""
        )

        try:
            response = self.api.place_order(order_req)
            self._pending_orders[response.order_id] = response
            self._log_order(response)
            logger.success(
                "매수 주문 접수 [{}] {} x {} @ ${:.2f}",
                response.order_id, signal.symbol, quantity, price
            )
            return response
        except Exception as e:
            logger.error("매수 주문 실패 [{}]: {}", signal.symbol, e)
            return None

    def execute_sell(self, position: Position, reason: str = "") -> Optional[OrderResponse]:
        """매도 주문 실행 (전량)"""
        if position.quantity <= 0:
            return None

        if self._has_pending_order(position.symbol, OrderSide.SELL):
            logger.info("이미 매도 주문 대기 중: {}", position.symbol)
            return None

        price = position.current_price
        if self.order_type != OrderType.MARKET:
            price = position.current_price * (1 - self.slippage_pct / 100)

        order_req = OrderRequest(
            symbol=position.symbol,
            market=position.market,
            side=OrderSide.SELL,
            order_type=self.order_type,
            quantity=position.quantity,
            price=round(price, 2),
            strategy_name=position.strategy_name,
            memo=reason[:50] if reason else "전략 매도"
        )

        try:
            response = self.api.place_order(order_req)
            self._pending_orders[response.order_id] = response
            self._log_order(response)
            logger.success(
                "매도 주문 접수 [{}] {} x {} @ ${:.2f} ({})",
                response.order_id, position.symbol, position.quantity, price, reason
            )
            return response
        except Exception as e:
            logger.error("매도 주문 실패 [{}]: {}", position.symbol, e)
            return None

    def check_pending_orders(self) -> List[OrderResponse]:
        """미체결 주문 상태 확인 및 업데이트"""
        filled = []
        to_remove = []

        for order_id, order in self._pending_orders.items():
            try:
                status = self.api.check_order_status(order_id, order.market)
                order.status = status

                if status == OrderStatus.FILLED:
                    order.filled_at = datetime.now()
                    filled.append(order)
                    self._filled_orders.append(order)
                    to_remove.append(order_id)
                    logger.info("주문 체결 완료: {} {} {}주", order.symbol, order.side.name, order.quantity)

                elif status == OrderStatus.CANCELLED:
                    to_remove.append(order_id)
                    logger.warning("주문 취소됨: {}", order_id)

                # 30분 이상 미체결 주문 취소
                elapsed = (datetime.now() - order.submitted_at).total_seconds()
                if elapsed > 1800 and status == OrderStatus.SUBMITTED:
                    self.api.cancel_order(order_id, order.symbol, order.market, order.quantity)
                    to_remove.append(order_id)
                    logger.warning("30분 경과 미체결 주문 취소: {}", order_id)

            except Exception as e:
                logger.error("주문 상태 확인 실패 [{}]: {}", order_id, e)

        for order_id in to_remove:
            self._pending_orders.pop(order_id, None)

        return filled

    def _has_pending_order(self, symbol: str, side: OrderSide) -> bool:
        return any(
            o.symbol == symbol and o.side == side
            for o in self._pending_orders.values()
        )

    def _log_order(self, order: OrderResponse):
        """주문 내역을 JSONL 파일에 기록"""
        try:
            record = {
                "timestamp": datetime.now().isoformat(),
                "order_id": order.order_id,
                "symbol": order.symbol,
                "market": order.market,
                "side": order.side.value,
                "order_type": order.order_type.value,
                "quantity": order.quantity,
                "price": order.price,
                "status": order.status.value
            }
            with open(self._order_log_path, "a") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.debug("주문 로그 기록 오류: {}", e)

    def get_pending_count(self) -> int:
        return len(self._pending_orders)

    def get_today_orders(self) -> List[OrderResponse]:
        today = datetime.now().date()
        return [o for o in self._filled_orders if o.submitted_at.date() == today]

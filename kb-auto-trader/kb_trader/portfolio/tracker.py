"""포트폴리오 추적 및 분석"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from loguru import logger

from ..api.client import KBApiClient
from ..api.models import Balance, Position


class PortfolioTracker:
    """
    포트폴리오 현황 추적
    - 실시간 PnL 계산
    - 일별 성과 기록
    - 섹터 집중도 분석
    """

    def __init__(self, api_client: KBApiClient, db_path: str = "data/trading.db"):
        self.api = api_client
        self._positions: Dict[str, Position] = {}
        self._balance: Optional[Balance] = None
        self._daily_snapshots: List[Dict] = []
        self._snapshot_path = Path("data/portfolio_snapshots.jsonl")
        self._snapshot_path.parent.mkdir(exist_ok=True)
        self._load_snapshots()

    def refresh(self) -> Tuple[Balance, List[Position]]:
        """API로 잔고/포지션 갱신"""
        try:
            self._balance = self.api.get_balance()
            api_positions = self.api.get_positions()

            for pos in api_positions:
                if pos.symbol in self._positions:
                    existing = self._positions[pos.symbol]
                    pos.stop_loss = existing.stop_loss
                    pos.take_profit = existing.take_profit
                    pos.trailing_stop = existing.trailing_stop
                    pos.highest_price = max(existing.highest_price, pos.current_price)
                    pos.strategy_name = existing.strategy_name
                    pos.entry_date = existing.entry_date
                self._positions[pos.symbol] = pos

            # 청산된 포지션 제거
            api_symbols = {p.symbol for p in api_positions}
            self._positions = {k: v for k, v in self._positions.items() if k in api_symbols}

            return self._balance, list(self._positions.values())
        except Exception as e:
            logger.error("포트폴리오 갱신 실패: {}", e)
            return self._balance, list(self._positions.values())

    def add_position(self, symbol: str, market: str, quantity: int,
                      avg_price: float, strategy_name: str,
                      stop_loss: float, take_profit: float):
        """새 포지션 추가"""
        pos = Position(
            symbol=symbol,
            market=market,
            quantity=quantity,
            avg_price=avg_price,
            current_price=avg_price,
            entry_date=datetime.now(),
            strategy_name=strategy_name,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=stop_loss,
            highest_price=avg_price
        )
        self._positions[symbol] = pos
        self._save_position(pos)
        logger.info("포지션 추가: {} {}주 @ ${:.2f}", symbol, quantity, avg_price)

    def update_prices(self, prices: Dict[str, float]):
        """현재가 일괄 업데이트"""
        for symbol, price in prices.items():
            if symbol in self._positions:
                self._positions[symbol].current_price = price
                if price > self._positions[symbol].highest_price:
                    self._positions[symbol].highest_price = price

    def remove_position(self, symbol: str):
        """포지션 제거 (청산 후)"""
        if symbol in self._positions:
            del self._positions[symbol]

    def get_total_pnl(self) -> Tuple[float, float]:
        """전체 미실현 손익 계산 (금액, %)"""
        total_cost = sum(p.cost_basis for p in self._positions.values())
        total_value = sum(p.market_value for p in self._positions.values())
        pnl = total_value - total_cost
        pnl_pct = (pnl / total_cost * 100) if total_cost > 0 else 0.0
        return pnl, pnl_pct

    def get_portfolio_summary(self) -> Dict:
        """포트폴리오 요약 정보"""
        positions = list(self._positions.values())
        total_pnl, total_pnl_pct = self.get_total_pnl()

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_assets": self._balance.total_assets if self._balance else 0,
            "cash": self._balance.cash if self._balance else 0,
            "stock_value": sum(p.market_value for p in positions),
            "position_count": len(positions),
            "total_unrealized_pnl": total_pnl,
            "total_unrealized_pnl_pct": total_pnl_pct,
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "avg_price": p.avg_price,
                    "current_price": p.current_price,
                    "market_value": p.market_value,
                    "unrealized_pnl": p.unrealized_pnl,
                    "unrealized_pnl_pct": p.unrealized_pnl_pct,
                    "strategy": p.strategy_name,
                    "stop_loss": p.stop_loss,
                    "take_profit": p.take_profit
                }
                for p in positions
            ]
        }
        return summary

    def save_daily_snapshot(self):
        """일별 포트폴리오 스냅샷 저장"""
        snapshot = self.get_portfolio_summary()
        snapshot["date"] = date.today().isoformat()
        self._daily_snapshots.append(snapshot)

        with open(self._snapshot_path, "a") as f:
            f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
        logger.info("포트폴리오 스냅샷 저장 완료")

    def get_performance_history(self, days: int = 30) -> pd.DataFrame:
        """성과 히스토리 DataFrame 반환"""
        if not self._daily_snapshots:
            return pd.DataFrame()

        records = self._daily_snapshots[-days:]
        df = pd.DataFrame([{
            "date": r.get("date", ""),
            "total_assets": r.get("total_assets", 0),
            "stock_value": r.get("stock_value", 0),
            "unrealized_pnl": r.get("total_unrealized_pnl", 0),
            "pnl_pct": r.get("total_unrealized_pnl_pct", 0)
        } for r in records])

        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df.sort_values("date", inplace=True)
        return df

    def _load_snapshots(self):
        """저장된 스냅샷 로드"""
        if self._snapshot_path.exists():
            with open(self._snapshot_path) as f:
                for line in f:
                    try:
                        self._daily_snapshots.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    def _save_position(self, pos: Position):
        """포지션 파일에 기록"""
        pos_path = Path("data/positions.jsonl")
        record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": pos.symbol,
            "market": pos.market,
            "quantity": pos.quantity,
            "avg_price": pos.avg_price,
            "strategy": pos.strategy_name,
            "stop_loss": pos.stop_loss,
            "take_profit": pos.take_profit
        }
        with open(pos_path, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

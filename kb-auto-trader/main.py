"""
KB증권 해외주식 자동매매 시스템 - 메인 실행 파일
사용법: python main.py [--paper] [--config config/config.yaml]
"""

import argparse
import os
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv
from loguru import logger

from kb_trader.api.client import KBApiClient
from kb_trader.api.models import OrderSide, Position
from kb_trader.notification.telegram import TelegramNotifier
from kb_trader.order.manager import OrderManager
from kb_trader.portfolio.tracker import PortfolioTracker
from kb_trader.risk.manager import RiskManager
from kb_trader.strategies import (
    STRATEGY_REGISTRY, CombinedStrategy, BaseStrategy
)
from kb_trader.utils.logger import setup_logger
from kb_trader.utils.market_hours import MarketHoursChecker


load_dotenv()


def load_config(path: str = "config/config.yaml") -> dict:
    """설정 파일 로드 (환경변수 치환)"""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    for key, value in os.environ.items():
        content = content.replace(f"${{{key}}}", value)

    return yaml.safe_load(content)


class KBAutoTrader:
    """KB증권 해외주식 자동매매 메인 엔진"""

    def __init__(self, config: dict):
        self.config = config
        self._running = False

        # API 설정
        api_cfg = config["api"]
        is_paper = api_cfg.get("is_paper_trading", True)

        # 컴포넌트 초기화
        self.api = KBApiClient(
            app_key=api_cfg["app_key"],
            app_secret=api_cfg["app_secret"],
            account_number=api_cfg["account_number"],
            base_url=api_cfg.get("base_url", "https://openapi.kbsec.com"),
            is_paper=is_paper
        )

        self.market_checker = MarketHoursChecker(
            config["scheduler"].get("timezone", "America/New_York")
        )
        self.risk_manager = RiskManager(config["risk"])
        self.order_manager = OrderManager(self.api, config["trading"])
        self.portfolio = PortfolioTracker(self.api)
        self.notifier = TelegramNotifier(
            bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            enabled=config["notification"]["telegram"].get("enabled", False)
        )

        # 전략 초기화
        self.strategy = self._build_strategy()

        # 감시 종목
        self.watchlist: List[str] = config["trading"].get("watchlist", [])
        self.market = config["trading"].get("market", "NASD")

        # 가격 캐시
        self._prices: Dict[str, float] = {}
        self._price_history: Dict[str, list] = {}

        mode = "모의투자" if is_paper else "실거래"
        logger.info("KB 자동매매 초기화 완료 ({})", mode)

    def _build_strategy(self) -> CombinedStrategy:
        """설정 파일에서 전략 로드 및 결합"""
        active = self.config["strategies"]["active"]
        method = self.config["strategies"].get("signal_combine", "weighted")
        min_score = self.config["strategies"].get("min_signal_score", 0.6)

        strategy_list = []
        for item in active:
            name = item["name"]
            weight = item.get("weight", 1.0)
            params = item.get("params", {})

            if name in STRATEGY_REGISTRY:
                strategy_list.append((STRATEGY_REGISTRY[name](params), weight))
                logger.info("전략 로드: {} (weight={})", name, weight)
            else:
                logger.warning("알 수 없는 전략: {}", name)

        return CombinedStrategy(strategy_list, method, min_score)

    # ── 메인 루프 ─────────────────────────────────────────────────────

    def start(self):
        """자동매매 시작"""
        self._running = True
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        logger.success("=" * 60)
        logger.success("KB증권 해외주식 자동매매 시스템 시작")
        logger.success("감시 종목: {}", ", ".join(self.watchlist))
        logger.success("=" * 60)

        self.notifier.notify_startup(
            "paper" if self.api.is_paper else "live",
            self.watchlist
        )

        # 토큰 발급
        self.api.get_access_token()

        while self._running:
            try:
                self._run_cycle()
                interval = self.config["scheduler"]["jobs"][0].get("interval_seconds", 60)
                time.sleep(interval)
            except Exception as e:
                logger.exception("사이클 오류: {}", e)
                self.notifier.notify_system_error(str(e))
                time.sleep(30)

    def _run_cycle(self):
        """단일 매매 사이클"""
        market_status = self.market_checker.get_status()
        logger.debug("시장 상태: {}", market_status)

        # 시장이 열려 있을 때만 실행 (프리마켓 포함)
        if not (self.market_checker.is_market_open() or
                self.market_checker.is_pre_market()):
            return

        # 1. 포트폴리오 갱신
        balance, positions = self.portfolio.refresh()
        if balance is None:
            logger.warning("잔고 조회 실패")
            return

        # 2. 리스크 체크
        ok, msg = self.risk_manager.check_portfolio_risk(balance)
        if not ok:
            logger.critical("포트폴리오 리스크 위반: {}", msg)
            self.notifier.notify_risk_alert(msg)
            return

        # 3. 시세 조회
        prices = self.api.get_multiple_prices(self.watchlist, self.market)
        current_prices = {sym: p.current_price for sym, p in prices.items()}
        self.portfolio.update_prices(current_prices)

        # 4. 보유 포지션 청산 조건 체크
        for pos in positions:
            self._check_position_exit(pos)

        # 5. 체결 대기 주문 확인
        self.order_manager.check_pending_orders()

        # 6. 신규 진입 신호 생성
        if not self.risk_manager.is_halted:
            for symbol in self.watchlist:
                if symbol not in current_prices:
                    continue
                if any(p.symbol == symbol for p in positions):
                    continue  # 이미 보유 중

                self._check_entry(symbol, current_prices[symbol], balance, positions)

    def _check_position_exit(self, pos: Position):
        """포지션 청산 조건 확인"""
        should_exit, reason = self.risk_manager.check_exit_conditions(pos)
        if should_exit:
            logger.info("청산 신호 [{}]: {}", pos.symbol, reason)
            response = self.order_manager.execute_sell(pos, reason)
            if response:
                if "손절" in reason:
                    self.notifier.notify_stop_loss(
                        pos.symbol, pos.avg_price,
                        pos.current_price, pos.unrealized_pnl_pct
                    )
                elif "수익실현" in reason:
                    self.notifier.notify_take_profit(
                        pos.symbol, pos.avg_price,
                        pos.current_price, pos.unrealized_pnl_pct
                    )
                self.portfolio.remove_position(pos.symbol)

    def _check_entry(self, symbol: str, current_price: float,
                      balance, positions: List[Position]):
        """신규 진입 체크"""
        hist_data = self._get_price_history(symbol)
        if hist_data is None or len(hist_data) < 30:
            return

        import pandas as pd
        df = pd.DataFrame(hist_data)

        signal = self.strategy.generate_signal(symbol, df, current_price)
        if signal is None or not signal.is_buy:
            return

        logger.info("매수 신호 [{}]: {} (강도: {:.2f})", symbol, signal.reason, signal.strength)

        # 포지션 사이징
        quantity, invest_amount = self.risk_manager.calculate_position_size(
            balance.cash, current_price
        )

        can_open, deny_reason = self.risk_manager.can_open_position(
            balance, positions, invest_amount
        )
        if not can_open:
            logger.debug("포지션 불가 [{}]: {}", symbol, deny_reason)
            return

        # 주문 실행
        stop_loss, take_profit, _ = self.risk_manager.calculate_exits(current_price)
        response = self.order_manager.execute_buy(signal, quantity, stop_loss, take_profit)

        if response:
            self.portfolio.add_position(
                symbol, self.market, quantity, current_price,
                signal.strategy_name, stop_loss, take_profit
            )
            self.notifier.notify_order_placed(
                symbol, "BUY", quantity, current_price, signal.strategy_name
            )

    def _get_price_history(self, symbol: str) -> Optional[list]:
        """일봉 히스토리 데이터 조회 (캐시 포함)"""
        try:
            raw = self.api.get_overseas_daily_price(symbol, self.market, count=100)
            if not raw:
                return None

            history = []
            for item in reversed(raw):
                try:
                    history.append({
                        "date": item.get("xymd", ""),
                        "open": float(item.get("open", 0)),
                        "high": float(item.get("high", 0)),
                        "low": float(item.get("low", 0)),
                        "close": float(item.get("clos", 0)),
                        "volume": int(item.get("tvol", 0))
                    })
                except (ValueError, TypeError):
                    pass
            return history if len(history) >= 30 else None
        except Exception as e:
            logger.debug("히스토리 조회 실패 [{}]: {}", symbol, e)
            return None

    def _handle_shutdown(self, signum, frame):
        """종료 처리"""
        logger.warning("종료 신호 수신 - 안전하게 종료합니다...")
        self._running = False
        self.portfolio.save_daily_snapshot()
        logger.info("포트폴리오 스냅샷 저장 완료")
        sys.exit(0)

    def send_daily_report(self):
        """일간 리포트 전송"""
        summary = self.portfolio.get_portfolio_summary()
        today_orders = self.order_manager.get_today_orders()
        pnl, pnl_pct = self.portfolio.get_total_pnl()

        self.notifier.notify_daily_report(
            total_assets=summary.get("total_assets", 0),
            daily_pnl=pnl,
            daily_pnl_pct=pnl_pct,
            position_count=summary.get("position_count", 0),
            today_trades=len(today_orders)
        )
        self.portfolio.save_daily_snapshot()
        self.risk_manager.reset_daily()


def main():
    parser = argparse.ArgumentParser(description="KB증권 해외주식 자동매매 시스템")
    parser.add_argument("--config", default="config/config.yaml", help="설정 파일 경로")
    parser.add_argument("--paper", action="store_true", help="모의투자 모드 강제 적용")
    parser.add_argument("--log-level", default="INFO", help="로그 레벨")
    args = parser.parse_args()

    # 로거 초기화
    setup_logger(level=args.log_level)

    # 설정 로드
    config = load_config(args.config)
    if args.paper:
        config["api"]["is_paper_trading"] = True

    mode = "모의투자" if config["api"].get("is_paper_trading", True) else "실거래"
    logger.warning("실행 모드: {}", mode)

    if not config["api"].get("is_paper_trading", True):
        logger.critical("⚠️  실거래 모드입니다! 실제 자금이 거래됩니다.")
        confirm = input("계속 진행하시겠습니까? (yes/no): ")
        if confirm.lower() != "yes":
            sys.exit(0)

    trader = KBAutoTrader(config)
    trader.start()


if __name__ == "__main__":
    main()

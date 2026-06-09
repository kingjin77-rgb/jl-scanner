"""
백테스트 실행기
사용법: python backtest_runner.py --strategy RSIStrategy --start 2023-01-01 --end 2024-12-31
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import pandas as pd
import numpy as np
from loguru import logger

from kb_trader.backtest.engine import BacktestEngine
from kb_trader.backtest.analyzer import BacktestAnalyzer
from kb_trader.strategies import STRATEGY_REGISTRY, CombinedStrategy
from kb_trader.utils.logger import setup_logger


def generate_mock_data(symbols: list, start: str, end: str) -> Dict[str, pd.DataFrame]:
    """모의 OHLCV 데이터 생성 (실제 API 데이터 없을 때 테스트용)"""
    dates = pd.date_range(start, end, freq="B")
    data = {}

    seed_prices = {
        "AAPL": 150.0, "MSFT": 250.0, "NVDA": 200.0,
        "GOOGL": 100.0, "AMZN": 130.0, "META": 200.0,
        "TSLA": 200.0, "AVGO": 600.0, "AMD": 100.0, "INTC": 50.0
    }

    np.random.seed(42)
    for sym in symbols:
        base = seed_prices.get(sym, 100.0)
        returns = np.random.normal(0.0003, 0.02, len(dates))
        closes = base * np.cumprod(1 + returns)

        df = pd.DataFrame({
            "open": closes * np.random.uniform(0.99, 1.01, len(dates)),
            "high": closes * np.random.uniform(1.005, 1.03, len(dates)),
            "low": closes * np.random.uniform(0.97, 0.995, len(dates)),
            "close": closes,
            "volume": np.random.randint(1_000_000, 50_000_000, len(dates))
        }, index=dates)

        df["high"] = df[["open", "close", "high"]].max(axis=1)
        df["low"] = df[["open", "close", "low"]].min(axis=1)
        data[sym] = df

    return data


def run_backtest(strategy_name: str, symbols: list,
                  start: str, end: str, capital: float,
                  stop_loss: float, take_profit: float,
                  use_mock: bool = True):
    """백테스트 실행"""

    if strategy_name not in STRATEGY_REGISTRY and strategy_name != "Combined":
        logger.error("알 수 없는 전략: {}. 가능한 전략: {}", strategy_name, list(STRATEGY_REGISTRY.keys()))
        sys.exit(1)

    # 데이터 로드 (모의 또는 실제)
    logger.info("데이터 로드 중: {} ~ {}", start, end)
    if use_mock:
        logger.warning("모의 데이터 사용 (실제 백테스트는 실제 데이터 필요)")
        data = generate_mock_data(symbols, start, end)
    else:
        # 실제 데이터 로드 로직
        data = {}
        logger.warning("실제 데이터 로드는 API 연결 필요")

    # 전략 인스턴스 생성
    if strategy_name == "Combined":
        strategies = [(cls({}), 1.0) for cls in STRATEGY_REGISTRY.values()]
        strategy = CombinedStrategy(strategies, "weighted", 0.6)
        strategy.name = "CombinedStrategy"
    else:
        strategy = STRATEGY_REGISTRY[strategy_name]({})

    # 엔진 실행
    engine = BacktestEngine(
        initial_capital=capital,
        commission_pct=0.25,
        slippage_pct=0.05,
        stop_loss_pct=stop_loss,
        take_profit_pct=take_profit,
        position_size_pct=10.0
    )

    logger.info("백테스트 실행 중: {} / {} 종목", strategy_name, len(symbols))
    result = engine.run(data, strategy)

    # 결과 분석
    analyzer = BacktestAnalyzer(result)
    analyzer.print_summary()

    # 월별 수익률
    monthly = analyzer.get_monthly_returns()
    if not monthly.empty:
        logger.info("\n📅 월별 수익률:\n{}", monthly.to_string())

    # 리포트 저장
    Path("data").mkdir(exist_ok=True)
    report_path = f"data/backtest_{strategy_name}_{start}_{end}.xlsx"
    analyzer.save_report(report_path)

    return result


def main():
    parser = argparse.ArgumentParser(description="KB 자동매매 백테스터")
    parser.add_argument("--strategy", default="Combined",
                        help=f"전략 이름: {list(STRATEGY_REGISTRY.keys())} 또는 Combined")
    parser.add_argument("--start", default="2023-01-01", help="백테스트 시작일 (YYYY-MM-DD)")
    parser.add_argument("--end", default="2024-12-31", help="백테스트 종료일 (YYYY-MM-DD)")
    parser.add_argument("--capital", type=float, default=100000.0, help="초기 자본 (USD)")
    parser.add_argument("--stop-loss", type=float, default=3.0, help="손절 비율 (%)")
    parser.add_argument("--take-profit", type=float, default=8.0, help="수익실현 비율 (%)")
    parser.add_argument("--symbols", nargs="+",
                        default=["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"],
                        help="백테스트 종목 목록")
    parser.add_argument("--mock", action="store_true", default=True, help="모의 데이터 사용")
    args = parser.parse_args()

    setup_logger(level="INFO")

    run_backtest(
        strategy_name=args.strategy,
        symbols=args.symbols,
        start=args.start,
        end=args.end,
        capital=args.capital,
        stop_loss=args.stop_loss,
        take_profit=args.take_profit,
        use_mock=args.mock
    )


if __name__ == "__main__":
    main()

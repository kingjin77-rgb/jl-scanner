"""백테스트 결과 분석 및 리포트"""

from typing import Optional

import pandas as pd
import numpy as np
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich import box

from .engine import BacktestResult


console = Console()


class BacktestAnalyzer:
    """백테스트 결과 분석 및 시각화"""

    def __init__(self, result: BacktestResult):
        self.result = result

    def print_summary(self):
        """콘솔에 요약 출력"""
        r = self.result

        table = Table(
            title="📊 백테스트 결과 요약",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("지표", style="bold", width=25)
        table.add_column("값", justify="right", width=20)

        color = "green" if r.total_return >= 0 else "red"
        table.add_row("초기 자본", f"${r.initial_capital:,.0f}")
        table.add_row("최종 자본", f"${r.final_capital:,.0f}")
        table.add_row(
            "총 수익률",
            f"[{color}]{r.total_return_pct:+.2f}%[/{color}]"
        )
        table.add_row("샤프 비율", f"{r.sharpe_ratio:.2f}")
        table.add_row("소르티노 비율", f"{r.sortino_ratio:.2f}")
        table.add_row(
            "최대 낙폭 (MDD)",
            f"[red]{r.max_drawdown_pct:.1f}%[/red]"
        )
        table.add_row("총 거래 횟수", f"{r.total_trades:,}회")
        table.add_row(
            "승률",
            f"[green]{r.win_rate:.1f}%[/green]"
        )
        table.add_row("수익 팩터", f"{r.profit_factor:.2f}")
        table.add_row("평균 수익", f"${r.avg_win:,.0f}")
        table.add_row("평균 손실", f"${r.avg_loss:,.0f}")
        table.add_row(
            "손익비",
            f"{r.avg_win / r.avg_loss:.2f}" if r.avg_loss > 0 else "∞"
        )
        table.add_row("평균 보유 기간", f"{r.avg_holding_days:.1f}일")

        console.print(table)

    def get_monthly_returns(self) -> pd.DataFrame:
        """월별 수익률 테이블"""
        if self.result.equity_curve.empty:
            return pd.DataFrame()

        monthly = self.result.equity_curve.resample("ME").last().pct_change() * 100
        monthly.index = monthly.index.to_period("M")
        return monthly.to_frame(name="수익률(%)")

    def get_trade_analysis(self) -> pd.DataFrame:
        """거래 내역 분석 DataFrame"""
        if not self.result.trades:
            return pd.DataFrame()

        records = []
        for t in self.result.trades:
            records.append({
                "종목": t.symbol,
                "매수일": t.entry_date,
                "매도일": t.exit_date,
                "보유일": t.holding_days,
                "매수가": t.entry_price,
                "매도가": t.exit_price,
                "수량": t.quantity,
                "손익($)": round(t.pnl, 2),
                "손익(%)": round(t.pnl_pct, 2),
                "청산사유": t.exit_reason
            })
        return pd.DataFrame(records)

    def save_report(self, path: str = "data/backtest_report.xlsx"):
        """엑셀 리포트 저장"""
        try:
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                summary_df = pd.DataFrame([{
                    "초기자본": self.result.initial_capital,
                    "최종자본": self.result.final_capital,
                    "총수익률(%)": self.result.total_return_pct,
                    "샤프비율": self.result.sharpe_ratio,
                    "MDD(%)": self.result.max_drawdown_pct,
                    "승률(%)": self.result.win_rate,
                    "수익팩터": self.result.profit_factor,
                    "총거래수": self.result.total_trades
                }])
                summary_df.to_excel(writer, sheet_name="요약", index=False)

                trade_df = self.get_trade_analysis()
                if not trade_df.empty:
                    trade_df.to_excel(writer, sheet_name="거래내역", index=False)

                monthly_df = self.get_monthly_returns()
                if not monthly_df.empty:
                    monthly_df.to_excel(writer, sheet_name="월별수익률")

                equity_df = self.result.equity_curve.to_frame(name="자산")
                equity_df.to_excel(writer, sheet_name="자산곡선")

            logger.success("백테스트 리포트 저장: {}", path)
        except Exception as e:
            logger.error("리포트 저장 실패: {}", e)

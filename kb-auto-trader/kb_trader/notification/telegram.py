"""텔레그램 알림 모듈"""

import asyncio
from datetime import datetime
from typing import List, Optional

from loguru import logger

try:
    import telegram
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


class TelegramNotifier:
    """텔레그램 봇을 통한 실시간 알림"""

    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled and TELEGRAM_AVAILABLE and bool(bot_token)
        self._bot = None

        if self.enabled:
            try:
                self._bot = telegram.Bot(token=bot_token)
                logger.info("텔레그램 알림 활성화")
            except Exception as e:
                logger.warning("텔레그램 초기화 실패: {}", e)
                self.enabled = False

    def send(self, message: str, parse_mode: str = "Markdown"):
        """메시지 전송 (동기)"""
        if not self.enabled:
            logger.debug("텔레그램 알림 (비활성): {}", message[:50])
            return

        try:
            asyncio.run(self._send_async(message, parse_mode))
        except RuntimeError:
            # 이미 이벤트 루프가 실행 중인 경우
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._send_async(message, parse_mode))

    async def _send_async(self, message: str, parse_mode: str):
        try:
            await self._bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error("텔레그램 전송 실패: {}", e)

    # ── 알림 템플릿 ──────────────────────────────────────────────────

    def notify_order_placed(self, symbol: str, side: str, quantity: int,
                             price: float, strategy: str):
        msg = (
            f"📋 *주문 접수*\n"
            f"• 종목: `{symbol}`\n"
            f"• 구분: {'🔴 매수' if side == 'BUY' else '🔵 매도'}\n"
            f"• 수량: {quantity:,}주\n"
            f"• 가격: ${price:,.2f}\n"
            f"• 전략: {strategy}\n"
            f"• 시간: {datetime.now().strftime('%H:%M:%S')}"
        )
        self.send(msg)

    def notify_order_filled(self, symbol: str, side: str, quantity: int,
                             price: float, pnl: float = 0.0):
        emoji = "✅" if pnl >= 0 else "❌"
        pnl_str = f"+${pnl:,.0f}" if pnl >= 0 else f"-${abs(pnl):,.0f}"
        msg = (
            f"{emoji} *주문 체결*\n"
            f"• 종목: `{symbol}`\n"
            f"• 구분: {'매수' if side == 'BUY' else '매도'}\n"
            f"• 수량: {quantity:,}주\n"
            f"• 체결가: ${price:,.2f}\n"
        )
        if side == "SELL" and pnl != 0:
            msg += f"• 손익: *{pnl_str}*\n"
        msg += f"• 시간: {datetime.now().strftime('%H:%M:%S')}"
        self.send(msg)

    def notify_stop_loss(self, symbol: str, entry_price: float,
                          exit_price: float, loss_pct: float):
        msg = (
            f"🛑 *손절 실행*\n"
            f"• 종목: `{symbol}`\n"
            f"• 매수가: ${entry_price:,.2f}\n"
            f"• 손절가: ${exit_price:,.2f}\n"
            f"• 손실률: *{loss_pct:.1f}%*\n"
            f"• 시간: {datetime.now().strftime('%H:%M:%S')}"
        )
        self.send(msg)

    def notify_take_profit(self, symbol: str, entry_price: float,
                            exit_price: float, gain_pct: float):
        msg = (
            f"🎯 *수익실현*\n"
            f"• 종목: `{symbol}`\n"
            f"• 매수가: ${entry_price:,.2f}\n"
            f"• 매도가: ${exit_price:,.2f}\n"
            f"• 수익률: *+{gain_pct:.1f}%*\n"
            f"• 시간: {datetime.now().strftime('%H:%M:%S')}"
        )
        self.send(msg)

    def notify_daily_report(self, total_assets: float, daily_pnl: float,
                             daily_pnl_pct: float, position_count: int,
                             today_trades: int):
        emoji = "📈" if daily_pnl >= 0 else "📉"
        pnl_str = f"+${daily_pnl:,.0f}" if daily_pnl >= 0 else f"-${abs(daily_pnl):,.0f}"
        msg = (
            f"{emoji} *일간 리포트* ({datetime.now().strftime('%Y-%m-%d')})\n"
            f"━━━━━━━━━━━━━━━\n"
            f"• 총 자산: ${total_assets:,.0f}\n"
            f"• 일간 손익: *{pnl_str}* ({daily_pnl_pct:+.2f}%)\n"
            f"• 보유 종목: {position_count}개\n"
            f"• 오늘 거래: {today_trades}건\n"
            f"━━━━━━━━━━━━━━━"
        )
        self.send(msg)

    def notify_risk_alert(self, message: str):
        self.send(f"⚠️ *리스크 알림*\n{message}")

    def notify_system_error(self, error: str):
        self.send(f"🔥 *시스템 오류*\n```{error[:500]}```")

    def notify_startup(self, mode: str, watchlist: List[str]):
        mode_str = "🟡 모의투자" if mode == "paper" else "🟢 실거래"
        symbols = ", ".join(watchlist[:10])
        msg = (
            f"🚀 *KB 자동매매 시작*\n"
            f"• 모드: {mode_str}\n"
            f"• 감시 종목: {symbols}\n"
            f"• 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        self.send(msg)

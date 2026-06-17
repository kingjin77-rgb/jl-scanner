"""KB증권 WebSocket 실시간 시세 클라이언트"""

import asyncio
import json
import threading
from typing import Callable, Dict, List, Optional

import websockets
from loguru import logger

from .models import StockPrice


class KBWebSocketClient:
    """실시간 시세/체결 WebSocket 클라이언트"""

    def __init__(self, app_key: str, app_secret: str, access_token: str,
                 ws_url: str = "wss://openapi.kbsec.com/ws/v1"):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
        self.ws_url = ws_url

        self._ws = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._subscriptions: List[Dict] = []
        self._price_callbacks: Dict[str, List[Callable]] = {}
        self._order_callbacks: List[Callable] = []
        self._running = False
        self._reconnect_delay = 5

    def subscribe_price(self, symbol: str, market: str, callback: Callable):
        """실시간 시세 구독"""
        if symbol not in self._price_callbacks:
            self._price_callbacks[symbol] = []
        self._price_callbacks[symbol].append(callback)

        sub_data = {
            "header": {
                "approval_key": self.access_token,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "HDFSCNT0",   # 해외주식 실시간 체결가
                    "tr_key": f"{market}|{symbol}"
                }
            }
        }
        self._subscriptions.append(sub_data)
        logger.info("실시간 시세 구독 등록: {} ({})", symbol, market)

    def subscribe_orders(self, callback: Callable):
        """실시간 주문 체결 구독"""
        self._order_callbacks.append(callback)

    def start(self):
        """WebSocket 연결 시작 (별도 스레드)"""
        self._running = True
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True
        )
        self._thread.start()
        logger.info("WebSocket 클라이언트 시작")

    def stop(self):
        """WebSocket 연결 종료"""
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        logger.info("WebSocket 클라이언트 종료")

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_loop())

    async def _connect_loop(self):
        while self._running:
            try:
                await self._connect()
            except Exception as e:
                if self._running:
                    logger.warning("WebSocket 연결 끊김, {}초 후 재연결: {}", self._reconnect_delay, e)
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, 60)
            else:
                self._reconnect_delay = 5

    async def _connect(self):
        async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=10) as ws:
            self._ws = ws
            logger.info("WebSocket 연결 완료: {}", self.ws_url)

            for sub in self._subscriptions:
                await ws.send(json.dumps(sub))

            async for message in ws:
                if not self._running:
                    break
                await self._handle_message(message)

    async def _handle_message(self, message: str):
        try:
            if message.startswith("{"):
                data = json.loads(message)
                await self._process_json(data)
            else:
                # 파이프 구분 실시간 데이터
                parts = message.split("|")
                if len(parts) >= 4:
                    await self._process_realtime(parts)
        except Exception as e:
            logger.debug("WebSocket 메시지 처리 오류: {}", e)

    async def _process_json(self, data: Dict):
        header = data.get("header", {})
        tr_id = header.get("tr_id", "")
        rt_cd = header.get("tr_key", "")

        if data.get("body", {}).get("rt_cd") != "0":
            msg = data.get("body", {}).get("msg1", "")
            logger.warning("WebSocket 응답 오류: {}", msg)

    async def _process_realtime(self, parts: List[str]):
        """실시간 체결가 데이터 파싱"""
        tr_id = parts[1] if len(parts) > 1 else ""

        if tr_id == "HDFSCNT0":  # 해외주식 실시간 체결
            try:
                fields = parts[3].split("^")
                if len(fields) < 15:
                    return

                market_symbol = parts[2]
                market, symbol = market_symbol.split("|") if "|" in market_symbol else ("NASD", market_symbol)

                price_data = StockPrice(
                    symbol=symbol,
                    market=market,
                    current_price=float(fields[8]),
                    open_price=float(fields[9]),
                    high_price=float(fields[11]),
                    low_price=float(fields[12]),
                    prev_close=float(fields[13]),
                    volume=int(fields[14]),
                    change=float(fields[6]),
                    change_pct=float(fields[7]),
                )

                callbacks = self._price_callbacks.get(symbol, [])
                for cb in callbacks:
                    try:
                        cb(price_data)
                    except Exception as e:
                        logger.error("가격 콜백 오류 [{}]: {}", symbol, e)

            except (ValueError, IndexError) as e:
                logger.debug("실시간 데이터 파싱 오류: {}", e)

"""KB증권 REST API 클라이언트"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import (
    StockPrice, OrderRequest, OrderResponse, Balance,
    Position, OrderHistory, OrderSide, OrderStatus, OrderType
)


class KBApiClient:
    """KB증권 OpenAPI REST 클라이언트"""

    def __init__(self, app_key: str, app_secret: str, account_number: str,
                 base_url: str = "https://openapi.kbsec.com",
                 is_paper: bool = True):
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_number = account_number
        self.base_url = base_url
        self.is_paper = is_paper

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._session = requests.Session()
        self._session.headers.update({
            "content-type": "application/json; charset=utf-8",
            "User-Agent": "KB-AutoTrader/1.0"
        })

    # ── 인증 ───────────────────────────────────────────────────────────

    def _is_token_valid(self) -> bool:
        if not self._access_token or not self._token_expires_at:
            return False
        return datetime.now() < self._token_expires_at - timedelta(minutes=5)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_access_token(self) -> str:
        """OAuth2 액세스 토큰 발급"""
        if self._is_token_valid():
            return self._access_token

        url = f"{self.base_url}/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }

        resp = self._session.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 86400)
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        logger.info("KB증권 액세스 토큰 발급 완료 (만료: {})", self._token_expires_at)
        return self._access_token

    def _get_headers(self, tr_id: str) -> Dict[str, str]:
        """API 요청 공통 헤더 생성"""
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",  # P: 개인
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def _request(self, method: str, path: str, tr_id: str,
                 params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """공통 API 요청 처리"""
        url = f"{self.base_url}{path}"
        headers = self._get_headers(tr_id)

        try:
            if method == "GET":
                resp = self._session.get(url, headers=headers, params=params, timeout=15)
            else:
                resp = self._session.post(url, headers=headers, json=data, timeout=15)

            resp.raise_for_status()
            result = resp.json()

            if result.get("rt_cd") != "0":
                error_msg = result.get("msg1", "알 수 없는 오류")
                logger.error("API 오류 [{}]: {}", tr_id, error_msg)
                raise ValueError(f"API 오류: {error_msg}")

            return result

        except requests.exceptions.Timeout:
            logger.error("API 타임아웃: {} {}", method, path)
            raise
        except requests.exceptions.ConnectionError:
            logger.error("API 연결 오류: {} {}", method, path)
            raise

    # ── 시세 조회 ─────────────────────────────────────────────────────

    def get_overseas_price(self, symbol: str, market: str = "NASD") -> StockPrice:
        """해외주식 현재가 조회"""
        params = {
            "AUTH": "",
            "EXCD": market,
            "SYMB": symbol
        }
        result = self._request(
            "GET", "/uapi/overseas-price/v1/quotations/price",
            tr_id="HHDFS00000300", params=params
        )

        output = result.get("output", {})
        return StockPrice(
            symbol=symbol,
            market=market,
            current_price=float(output.get("last", 0)),
            open_price=float(output.get("open", 0)),
            high_price=float(output.get("high", 0)),
            low_price=float(output.get("low", 0)),
            prev_close=float(output.get("base", 0)),
            volume=int(output.get("tvol", 0)),
            change=float(output.get("diff", 0)),
            change_pct=float(output.get("rate", 0)),
            timestamp=datetime.now(),
            currency="USD"
        )

    def get_multiple_prices(self, symbols: List[str], market: str = "NASD") -> Dict[str, StockPrice]:
        """여러 종목 현재가 일괄 조회"""
        prices = {}
        for symbol in symbols:
            try:
                prices[symbol] = self.get_overseas_price(symbol, market)
                time.sleep(0.1)  # API 호출 속도 제한
            except Exception as e:
                logger.warning("시세 조회 실패 [{}]: {}", symbol, e)
        return prices

    def get_overseas_daily_price(self, symbol: str, market: str = "NASD",
                                  period: str = "D", count: int = 100) -> List[Dict]:
        """해외주식 일별/주별/월별 시세 조회"""
        params = {
            "AUTH": "",
            "EXCD": market,
            "SYMB": symbol,
            "GUBN": period,  # D: 일, W: 주, M: 월
            "BYMD": "",
            "MODP": "0",
            "COUNT": str(count)
        }
        result = self._request(
            "GET", "/uapi/overseas-price/v1/quotations/dailyprice",
            tr_id="HHDFS76240000", params=params
        )
        return result.get("output2", [])

    def get_exchange_rate(self, currency: str = "USD") -> float:
        """환율 조회"""
        try:
            params = {
                "TRCODE": "NFSFWQQ0601U00",
                "CUR_CD": currency
            }
            result = self._request(
                "GET", "/uapi/overseas-price/v1/quotations/exchange-rate",
                tr_id="CTRP6504R", params=params
            )
            return float(result.get("output", {}).get("bkpr", 1300.0))
        except Exception:
            return 1300.0  # 기본값

    # ── 잔고/포지션 조회 ──────────────────────────────────────────────

    def get_balance(self) -> Balance:
        """계좌 잔고 조회"""
        params = {
            "CANO": self.account_number[:8],
            "ACNT_PRDT_CD": self.account_number[-2:],
            "OVRS_EXCG_CD": "NASD",
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        tr_id = "VTTS3012R" if self.is_paper else "TTTS3012R"
        result = self._request(
            "GET", "/uapi/overseas-stock/v1/trading/inquire-balance",
            tr_id=tr_id, params=params
        )

        output2 = result.get("output2", [{}])
        summary = output2[0] if output2 else {}

        return Balance(
            total_assets=float(summary.get("tot_asst_amt", 0)),
            cash=float(summary.get("frcr_dncl_amt_2", 0)),
            stock_value=float(summary.get("tot_stck_evlu_amt", 0)),
            unrealized_pnl=float(summary.get("evlu_pfls_smtl_amt", 0)),
            realized_pnl=0.0,
            currency="USD",
            updated_at=datetime.now()
        )

    def get_positions(self) -> List[Position]:
        """보유 종목 조회"""
        params = {
            "CANO": self.account_number[:8],
            "ACNT_PRDT_CD": self.account_number[-2:],
            "OVRS_EXCG_CD": "NASD",
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        tr_id = "VTTS3012R" if self.is_paper else "TTTS3012R"
        result = self._request(
            "GET", "/uapi/overseas-stock/v1/trading/inquire-balance",
            tr_id=tr_id, params=params
        )

        positions = []
        for item in result.get("output1", []):
            if int(item.get("ovrs_cblc_qty", 0)) > 0:
                pos = Position(
                    symbol=item.get("ovrs_pdno", ""),
                    market=item.get("ovrs_excg_cd", "NASD"),
                    quantity=int(item.get("ovrs_cblc_qty", 0)),
                    avg_price=float(item.get("pchs_avg_pric", 0)),
                    current_price=float(item.get("now_pric2", 0)),
                    currency="USD",
                    entry_date=None
                )
                positions.append(pos)
        return positions

    # ── 주문 ──────────────────────────────────────────────────────────

    def place_order(self, order: OrderRequest) -> OrderResponse:
        """해외주식 주문 실행"""
        account_parts = self.account_number.split("-")
        cano = account_parts[0]
        acnt_prdt = account_parts[1] if len(account_parts) > 1 else "01"

        if order.side == OrderSide.BUY:
            tr_id = "VTTT1002U" if self.is_paper else "TTTT1002U"  # 매수
        else:
            tr_id = "VTTT1001U" if self.is_paper else "TTTT1006U"  # 매도

        payload = {
            "CANO": cano,
            "ACNT_PRDT_CD": acnt_prdt,
            "OVRS_EXCG_CD": order.market,
            "PDNO": order.symbol,
            "ORD_DVSN": order.order_type.value,
            "ORD_QTY": str(order.quantity),
            "OVRS_ORD_UNPR": str(order.price) if order.price > 0 else "0",
            "CTAC_TLNO": "",
            "MGCO_APTM_ODNO": "",
            "ORD_SVR_DVSN_CD": "0"
        }

        result = self._request(
            "POST", "/uapi/overseas-stock/v1/trading/order",
            tr_id=tr_id, data=payload
        )

        output = result.get("output", {})
        order_id = output.get("ODNO", f"MOCK-{int(time.time())}")

        logger.info(
            "주문 접수 [{}] {} {} {} @ ${:.2f}",
            order_id, order.side.name, order.quantity, order.symbol, order.price
        )

        return OrderResponse(
            order_id=order_id,
            symbol=order.symbol,
            market=order.market,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
            status=OrderStatus.SUBMITTED,
            submitted_at=datetime.now()
        )

    def cancel_order(self, order_id: str, symbol: str, market: str,
                     quantity: int) -> bool:
        """주문 취소"""
        account_parts = self.account_number.split("-")
        tr_id = "VTTT1004U" if self.is_paper else "TTTT1004U"

        payload = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1] if len(account_parts) > 1 else "01",
            "OVRS_EXCG_CD": market,
            "PDNO": symbol,
            "ORGN_ODNO": order_id,
            "RVSE_CNCL_DVSN_CD": "02",  # 02: 취소
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": "0",
            "MGCO_APTM_ODNO": ""
        }

        try:
            self._request(
                "POST", "/uapi/overseas-stock/v1/trading/order-rvsecncl",
                tr_id=tr_id, data=payload
            )
            logger.info("주문 취소 완료: {}", order_id)
            return True
        except Exception as e:
            logger.error("주문 취소 실패 [{}]: {}", order_id, e)
            return False

    def get_order_history(self, start_date: str = "", end_date: str = "",
                           market: str = "NASD") -> List[OrderHistory]:
        """주문 체결 내역 조회"""
        if not start_date:
            start_date = datetime.now().strftime("%Y%m%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        account_parts = self.account_number.split("-")
        tr_id = "VTTS3035R" if self.is_paper else "TTTS3035R"

        params = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1] if len(account_parts) > 1 else "01",
            "PDNO": "%",
            "OVRS_EXCG_CD": market,
            "ORD_STRT_DT": start_date,
            "ORD_END_DT": end_date,
            "SLL_BUY_DVSN": "00",
            "CCL_NCCS_DVSN": "00",
            "OVRS_ORD_UNPR_DVSN": "0",
            "SORT_SQN": "DS",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }

        result = self._request(
            "GET", "/uapi/overseas-stock/v1/trading/inquire-ccnl",
            tr_id=tr_id, params=params
        )

        orders = []
        for item in result.get("output", []):
            orders.append(OrderHistory(
                order_id=item.get("odno", ""),
                symbol=item.get("pdno", ""),
                market=item.get("ovrs_excg_cd", ""),
                side=OrderSide.BUY if item.get("sll_buy_dvsn_cd") == "02" else OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=int(item.get("ft_ord_qty", 0)),
                price=float(item.get("ft_ord_unpr3", 0)),
                filled_price=float(item.get("ft_ccld_unpr3", 0)),
                filled_quantity=int(item.get("ft_ccld_qty", 0)),
                status=OrderStatus.FILLED,
                commission=0.0,
                created_at=datetime.strptime(
                    item.get("ord_dt", datetime.now().strftime("%Y%m%d")), "%Y%m%d"
                )
            ))
        return orders

    def check_order_status(self, order_id: str, market: str = "NASD") -> OrderStatus:
        """주문 상태 확인"""
        account_parts = self.account_number.split("-")
        tr_id = "VTTS3014R" if self.is_paper else "TTTS3014R"

        params = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1] if len(account_parts) > 1 else "01",
            "OVRS_EXCG_CD": market,
            "SORT_SQN": "DS",
            "ODNO": order_id,
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }

        try:
            result = self._request(
                "GET", "/uapi/overseas-stock/v1/trading/inquire-nccs",
                tr_id=tr_id, params=params
            )
            items = result.get("output", [])
            if not items:
                return OrderStatus.FILLED
            item = items[0]
            ord_stat = item.get("ord_stat_cd", "")
            if ord_stat in ("02", "03"):
                return OrderStatus.FILLED
            elif ord_stat == "01":
                return OrderStatus.SUBMITTED
            else:
                return OrderStatus.CANCELLED
        except Exception:
            return OrderStatus.PENDING

    def get_tradable_quantity(self, symbol: str, market: str, price: float,
                               side: OrderSide) -> int:
        """주문 가능 수량 조회"""
        account_parts = self.account_number.split("-")
        tr_id = "VTTS3007R" if self.is_paper else "TTTS3007R"

        params = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1] if len(account_parts) > 1 else "01",
            "OVRS_EXCG_CD": market,
            "OVRS_ORD_UNPR": str(price),
            "ITEM_AMT": "0",
            "PDNO": symbol,
            "ORD_DVSN": "00",
            "SLL_TYPE": "00"
        }

        try:
            result = self._request(
                "GET", "/uapi/overseas-stock/v1/trading/inquire-psamount",
                tr_id=tr_id, params=params
            )
            output = result.get("output", {})
            if side == OrderSide.BUY:
                return int(output.get("max_buy_qty", 0))
            else:
                return int(output.get("ovrs_max_ord_qty", 0))
        except Exception:
            return 0

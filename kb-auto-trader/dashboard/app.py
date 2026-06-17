"""
KB증권 해외주식 자동매매 - 실시간 모니터링 대시보드
실행: streamlit run dashboard/app.py
"""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yaml
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

# ── 페이지 설정 ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="KB 해외주식 자동매매",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 다크 테마 CSS ────────────────────────────────────────────────────

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252840);
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #3a3f5c;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .metric-title { color: #8b9dc3; font-size: 13px; font-weight: 500; }
    .metric-value { color: #ffffff; font-size: 24px; font-weight: 700; margin: 4px 0; }
    .metric-delta-pos { color: #00d27a; font-size: 13px; }
    .metric-delta-neg { color: #e0245e; font-size: 13px; }
    .position-row { border-bottom: 1px solid #252840; padding: 8px 0; }
    .status-live { color: #00d27a; }
    .status-paper { color: #f6c90e; }
    .sidebar .sidebar-content { background: #151822; }
    h1, h2, h3 { color: #ffffff; }
    .stDataFrame { background: #1e2130; }
</style>
""", unsafe_allow_html=True)


# ── 데이터 로더 ──────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_config():
    try:
        with open("config/config.yaml", encoding="utf-8") as f:
            content = f.read()
        for k, v in os.environ.items():
            content = content.replace(f"${{{k}}}", v)
        return yaml.safe_load(content)
    except Exception:
        return {}


@st.cache_data(ttl=30)
def load_portfolio_snapshots():
    path = Path("data/portfolio_snapshots.jsonl")
    if not path.exists():
        return pd.DataFrame()
    rows = []
    with open(path) as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


@st.cache_data(ttl=30)
def load_orders():
    path = Path("data/orders.jsonl")
    if not path.exists():
        return pd.DataFrame()
    rows = []
    with open(path) as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def try_api_fetch(config: dict) -> dict:
    """실제 API 연결 시도 (실패 시 캐시 사용)"""
    try:
        from kb_trader.api.client import KBApiClient
        api_cfg = config.get("api", {})
        client = KBApiClient(
            app_key=api_cfg.get("app_key", ""),
            app_secret=api_cfg.get("app_secret", ""),
            account_number=api_cfg.get("account_number", ""),
            base_url=api_cfg.get("base_url", "https://openapi.kbsec.com"),
            is_paper=api_cfg.get("is_paper_trading", True)
        )
        balance = client.get_balance()
        positions = client.get_positions()
        return {"balance": balance, "positions": positions, "connected": True}
    except Exception as e:
        return {"balance": None, "positions": [], "connected": False, "error": str(e)}


# ── 사이드바 ─────────────────────────────────────────────────────────

def render_sidebar(config: dict):
    with st.sidebar:
        st.image("https://via.placeholder.com/200x60/1e2130/4fc3f7?text=KB+AutoTrader",
                 use_container_width=True)
        st.markdown("---")

        is_paper = config.get("api", {}).get("is_paper_trading", True)
        mode_color = "status-paper" if is_paper else "status-live"
        mode_text = "모의투자" if is_paper else "실거래"
        st.markdown(f'<p class="{mode_color}">● {mode_text} 모드</p>', unsafe_allow_html=True)

        st.markdown("### ⚙️ 설정")
        watchlist = config.get("trading", {}).get("watchlist", [])
        st.write(f"감시 종목: {len(watchlist)}개")
        st.write(f"시장: {config.get('trading', {}).get('market', 'NASD')}")

        st.markdown("### 🛡️ 리스크 설정")
        risk = config.get("risk", {})
        st.write(f"손절선: {risk.get('stop_loss_pct', 3)}%")
        st.write(f"수익실현: {risk.get('take_profit_pct', 8)}%")
        st.write(f"최대 낙폭: {risk.get('max_drawdown_pct', 15)}%")
        st.write(f"최대 포지션: {config.get('trading', {}).get('max_positions', 10)}개")

        st.markdown("---")
        if st.button("🔄 데이터 새로고침"):
            st.cache_data.clear()
            st.rerun()

        from kb_trader.utils.market_hours import MarketHoursChecker
        checker = MarketHoursChecker()
        status = checker.get_status()
        st.markdown("### 🕐 시장 현황")
        st.write(status)


# ── 메인 대시보드 ─────────────────────────────────────────────────────

def render_overview(api_data: dict, snapshots_df: pd.DataFrame):
    st.markdown("## 📊 포트폴리오 현황")

    balance = api_data.get("balance")
    positions = api_data.get("positions", [])

    col1, col2, col3, col4, col5 = st.columns(5)

    total_assets = balance.total_assets if balance else 0
    cash = balance.cash if balance else 0
    stock_value = balance.stock_value if balance else 0
    unrealized = balance.unrealized_pnl if balance else 0
    unrealized_pct = (unrealized / (total_assets - unrealized) * 100) if (total_assets - unrealized) > 0 else 0

    with col1:
        st.metric("💰 총 자산", f"${total_assets:,.0f}", delta=None)
    with col2:
        st.metric("💵 현금", f"${cash:,.0f}")
    with col3:
        st.metric("📈 주식 평가액", f"${stock_value:,.0f}")
    with col4:
        delta_color = "normal" if unrealized >= 0 else "inverse"
        sign = "+" if unrealized >= 0 else ""
        st.metric("📊 미실현 손익",
                  f"{sign}${abs(unrealized):,.0f}",
                  delta=f"{sign}{unrealized_pct:.2f}%",
                  delta_color=delta_color)
    with col5:
        st.metric("🗂️ 보유 종목", f"{len(positions)}개")

    # 자산 변화 차트
    if not snapshots_df.empty and "total_assets" in snapshots_df.columns:
        st.markdown("### 📈 자산 변화")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=snapshots_df["timestamp"],
            y=snapshots_df["total_assets"],
            mode="lines+markers",
            name="총 자산",
            line=dict(color="#4fc3f7", width=2),
            fill="tozeroy",
            fillcolor="rgba(79, 195, 247, 0.1)"
        ))
        fig.update_layout(
            template="plotly_dark",
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="",
            yaxis_title="자산 ($)",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)


def render_positions(api_data: dict):
    positions = api_data.get("positions", [])
    st.markdown("## 📂 보유 포지션")

    if not positions:
        st.info("현재 보유 중인 종목이 없습니다.")
        return

    rows = []
    for pos in positions:
        pnl = pos.unrealized_pnl
        pnl_pct = pos.unrealized_pnl_pct
        rows.append({
            "종목": pos.symbol,
            "수량": pos.quantity,
            "평균단가": f"${pos.avg_price:,.2f}",
            "현재가": f"${pos.current_price:,.2f}",
            "평가금액": f"${pos.market_value:,.0f}",
            "손익($)": f"{'+'if pnl>=0 else ''}{pnl:,.0f}",
            "손익(%)": f"{'+'if pnl_pct>=0 else ''}{pnl_pct:.2f}%",
            "손절가": f"${pos.stop_loss:,.2f}" if pos.stop_loss > 0 else "-",
            "목표가": f"${pos.take_profit:,.2f}" if pos.take_profit > 0 else "-",
            "전략": pos.strategy_name
        })

    df = pd.DataFrame(rows)

    def color_pnl(val):
        if "+" in str(val):
            return "color: #00d27a"
        elif "-" in str(val) and val != "-":
            return "color: #e0245e"
        return ""

    styled = df.style.applymap(color_pnl, subset=["손익($)", "손익(%)"])
    st.dataframe(styled, use_container_width=True, height=300)

    # 파이 차트
    if len(rows) > 0:
        col1, col2 = st.columns(2)
        with col1:
            values = [pos.market_value for pos in positions]
            labels = [pos.symbol for pos in positions]
            fig = px.pie(values=values, names=labels, title="포트폴리오 구성",
                         template="plotly_dark", hole=0.4)
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            pnl_data = [(pos.symbol, pos.unrealized_pnl) for pos in positions]
            pnl_df = pd.DataFrame(pnl_data, columns=["종목", "손익"])
            colors = ["#00d27a" if v >= 0 else "#e0245e" for v in pnl_df["손익"]]
            fig = go.Figure(go.Bar(
                x=pnl_df["종목"], y=pnl_df["손익"],
                marker_color=colors
            ))
            fig.update_layout(
                title="종목별 손익 ($)", template="plotly_dark",
                height=300, margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)


def render_orders(orders_df: pd.DataFrame):
    st.markdown("## 📋 주문 내역")

    if orders_df.empty:
        st.info("주문 내역이 없습니다.")
        return

    recent = orders_df.sort_values("timestamp", ascending=False).head(50)

    # 오늘 통계
    today = datetime.now().date()
    today_orders = orders_df[orders_df["timestamp"].dt.date == today]
    buy_count = len(today_orders[today_orders["side"] == "02"])
    sell_count = len(today_orders[today_orders["side"] == "01"])

    col1, col2, col3 = st.columns(3)
    col1.metric("오늘 전체 주문", f"{len(today_orders)}건")
    col2.metric("매수", f"{buy_count}건")
    col3.metric("매도", f"{sell_count}건")

    st.dataframe(
        recent[["timestamp", "symbol", "side", "quantity", "price", "status"]].rename(
            columns={
                "timestamp": "시간", "symbol": "종목", "side": "구분",
                "quantity": "수량", "price": "가격", "status": "상태"
            }
        ),
        use_container_width=True
    )


def render_strategies():
    st.markdown("## 🧠 전략 신호")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 전략별 가중치")
        strategy_weights = {
            "Momentum": 0.35,
            "RSI": 0.30,
            "MACD": 0.20,
            "Bollinger": 0.15
        }
        fig = px.bar(
            x=list(strategy_weights.keys()),
            y=list(strategy_weights.values()),
            title="전략 가중치",
            template="plotly_dark",
            color=list(strategy_weights.values()),
            color_continuous_scale="blues"
        )
        fig.update_layout(height=300, showlegend=False,
                          margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 설정값")
        config = load_config()
        risk = config.get("risk", {})
        data = {
            "파라미터": ["손절선", "수익실현", "트레일링 스탑", "최대 낙폭", "포지션 사이저"],
            "값": [
                f"{risk.get('stop_loss_pct', 3)}%",
                f"{risk.get('take_profit_pct', 8)}%",
                f"{risk.get('trailing_stop_pct', 2)}%",
                f"{risk.get('max_drawdown_pct', 15)}%",
                risk.get("position_sizer", "kelly")
            ]
        }
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


def render_backtest_results():
    st.markdown("## 🔬 백테스트 결과")

    report_files = list(Path("data").glob("backtest_*.xlsx")) if Path("data").exists() else []
    if not report_files:
        st.info("백테스트 결과가 없습니다. `python backtest_runner.py` 를 먼저 실행하세요.")
        st.code("python backtest_runner.py --strategy Combined --start 2023-01-01 --end 2024-12-31")
        return

    selected = st.selectbox("리포트 선택", [f.name for f in report_files])
    if selected:
        df = pd.read_excel(f"data/{selected}", sheet_name="요약")
        st.dataframe(df, use_container_width=True)


# ── 메인 ─────────────────────────────────────────────────────────────

def main():
    config = load_config()
    render_sidebar(config)

    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 현황", "📂 포지션", "📋 주문내역", "🧠 전략", "🔬 백테스트"
    ])

    # API 데이터 (실패 시 빈 데이터)
    connected_placeholder = st.empty()
    api_data = try_api_fetch(config)

    if not api_data["connected"]:
        connected_placeholder.warning(
            f"⚠️ API 미연결 - 저장된 데이터를 표시합니다. "
            f"({api_data.get('error', '설정 확인 필요')})"
        )

    snapshots_df = load_portfolio_snapshots()
    orders_df = load_orders()

    with tab1:
        render_overview(api_data, snapshots_df)

    with tab2:
        render_positions(api_data)

    with tab3:
        render_orders(orders_df)

    with tab4:
        render_strategies()

    with tab5:
        render_backtest_results()

    # 자동 새로고침
    refresh_secs = config.get("dashboard", {}).get("refresh_seconds", 30)
    st.markdown(
        f'<p style="color:#555;font-size:11px;text-align:right;">'
        f'마지막 업데이트: {datetime.now().strftime("%H:%M:%S")} | '
        f'{refresh_secs}초마다 자동 갱신</p>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

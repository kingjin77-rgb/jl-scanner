"""
🏠 나만의 경매 분석기
경매 정보 수집 · 시세 분석 · 수익률 계산 · 알림
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
from pathlib import Path

from scrapers.court_auction import (
    fetch_court_auctions, COURT_CODES, ITEM_TYPE_CODES
)
from scrapers.onbid import fetch_onbid_auctions, REGION_CODES, ASSET_TYPES
from scrapers.moving_auction import (
    fetch_lost_property_auctions, fetch_moving_property_auctions
)
from analysis.profit_calculator import (
    calculate_profit, calculate_break_even
)
from analysis.market_analyzer import (
    analyze_by_type, analyze_by_region,
    filter_good_deals, get_price_distribution
)

# ── 페이지 설정 ────────────────────────────────────────
st.set_page_config(
    page_title="나만의 경매 분석기",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1E2130, #2A2F45);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 6px 0;
    border-left: 4px solid #FF6B35;
}
.metric-value { font-size: 1.6rem; font-weight: 700; color: #FF6B35; }
.metric-label { font-size: 0.85rem; color: #AAB0C0; }
.section-title {
    font-size: 1.1rem; font-weight: 700; color: #FF6B35;
    margin: 16px 0 8px; border-bottom: 2px solid #FF6B35; padding-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 헬퍼 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fmt_price(val: int) -> str:
    if val >= 100_000_000:
        return f"{val/100_000_000:.2f}억"
    elif val >= 10_000:
        return f"{val/10_000:.0f}만"
    return f"{val:,}원"


def load_watchlist() -> list:
    path = Path("watchlist.json")
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_watchlist(watchlist: list):
    Path("watchlist.json").write_text(
        json.dumps(watchlist, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def render_table(df: pd.DataFrame):
    """가격 포맷 적용 후 테이블 표시"""
    if df.empty:
        st.info("데이터가 없습니다.")
        return
    display = df.copy()
    for col in ["감정가", "최저매각가", "최저입찰가"]:
        if col in display.columns:
            display[col] = display[col].apply(
                lambda x: fmt_price(int(x)) if pd.notna(x) and str(x).replace('.', '').isdigit() and float(x) > 0 else "-"
            )
    st.dataframe(display, use_container_width=True, hide_index=True)


def add_to_collection(new_data: list, source: str):
    """수집 데이터를 세션에 추가"""
    if not new_data:
        st.warning("수집된 데이터가 없습니다.")
        return
    new_df = pd.DataFrame(new_data)
    new_df["출처"] = source
    st.session_state.collected_data = pd.concat(
        [st.session_state.collected_data, new_df], ignore_index=True
    )
    st.session_state.last_collected = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.success(f"✅ {len(new_data)}건 수집 완료!")


# ── 세션 상태 초기화 ───────────────────────────────────
if "watchlist" not in st.session_state:
    st.session_state.watchlist = load_watchlist()
if "collected_data" not in st.session_state:
    st.session_state.collected_data = pd.DataFrame()
if "last_collected" not in st.session_state:
    st.session_state.last_collected = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 사이드바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("## 🏠 경매 분석기")
    st.caption("경매 정보 수집 · 시세 분석 · 수익률")
    st.markdown("---")

    menu = st.radio(
        "메뉴",
        ["📡 경매 수집", "📊 시세 분석", "💰 수익률 계산기", "⭐ 관심 목록", "🔔 알림 설정"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    if not st.session_state.collected_data.empty:
        st.metric("수집 물건", f"{len(st.session_state.collected_data):,}건")
        if st.session_state.last_collected:
            st.caption(f"최근 수집: {st.session_state.last_collected}")
    st.metric("관심 목록", f"{len(st.session_state.watchlist)}건")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 경매 수집
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if menu == "📡 경매 수집":
    st.markdown("## 📡 경매 정보 수집")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["⚖️ 법원경매", "🏛️ 온비드 공매", "🚗 동산경매", "🔍 유실동산"]
    )

    with tab1:
        c1, c2, c3 = st.columns(3)
        court = c1.selectbox("법원", list(COURT_CODES.keys()))
        item_type_name = c2.selectbox("물건 종류", list(ITEM_TYPE_CODES.keys()))
        price_range = c3.select_slider(
            "최저가 범위 (억)", options=[0, 0.5, 1, 2, 3, 5, 10, 20, 50, 100], value=(0, 10)
        )
        if st.button("🔍 법원경매 수집", type="primary"):
            with st.spinner("수집 중..."):
                data = fetch_court_auctions(
                    court_code=COURT_CODES[court],
                    item_type=ITEM_TYPE_CODES[item_type_name],
                    min_price=int(price_range[0] * 1e8),
                    max_price=int(price_range[1] * 1e8),
                )
                add_to_collection(data, "법원경매")

        source_df = st.session_state.collected_data
        if not source_df.empty and "출처" in source_df.columns:
            filtered = source_df[source_df["출처"] == "법원경매"]
            if not filtered.empty:
                st.markdown(f"**법원경매 수집 ({len(filtered)}건)**")
                render_table(filtered.tail(20))

    with tab2:
        c1, c2, c3 = st.columns(3)
        ob_region = c1.selectbox("지역", list(REGION_CODES.keys()))
        ob_asset = c2.selectbox("자산 종류", list(ASSET_TYPES.keys()))
        ob_keyword = c3.text_input("검색어", placeholder="아파트, 토지")
        if st.button("🔍 온비드 수집", type="primary"):
            with st.spinner("수집 중..."):
                data = fetch_onbid_auctions(
                    asset_type=ASSET_TYPES[ob_asset],
                    region=REGION_CODES[ob_region],
                    keyword=ob_keyword,
                )
                add_to_collection(data, "온비드공매")

        source_df = st.session_state.collected_data
        if not source_df.empty and "출처" in source_df.columns:
            filtered = source_df[source_df["출처"] == "온비드공매"]
            if not filtered.empty:
                st.markdown(f"**온비드 공매 수집 ({len(filtered)}건)**")
                render_table(filtered.tail(20))

    with tab3:
        c1, c2 = st.columns(2)
        mv_keyword = c1.text_input("검색어", placeholder="차량, 포클레인")
        mv_category = c2.selectbox("분류", ["전체", "차량", "기계", "전자", "기타"])
        if st.button("🔍 동산경매 수집", type="primary"):
            with st.spinner("수집 중..."):
                data = fetch_moving_property_auctions(category=mv_category, keyword=mv_keyword)
                add_to_collection(data, "동산경매")

        source_df = st.session_state.collected_data
        if not source_df.empty and "출처" in source_df.columns:
            filtered = source_df[source_df["출처"] == "동산경매"]
            if not filtered.empty:
                st.markdown(f"**동산경매 수집 ({len(filtered)}건)**")
                render_table(filtered.tail(20))

    with tab4:
        lost_kw = st.text_input("검색어", placeholder="가방, 시계, 노트북")
        if st.button("🔍 유실동산 수집", type="primary"):
            with st.spinner("수집 중..."):
                data = fetch_lost_property_auctions(keyword=lost_kw)
                add_to_collection(data, "유실동산")

        source_df = st.session_state.collected_data
        if not source_df.empty and "출처" in source_df.columns:
            filtered = source_df[source_df["출처"] == "유실동산"]
            if not filtered.empty:
                st.markdown(f"**유실동산 수집 ({len(filtered)}건)**")
                render_table(filtered.tail(20))

    if not st.session_state.collected_data.empty:
        st.markdown("---")
        col_dl, col_reset = st.columns([1, 1])
        with col_dl:
            csv = st.session_state.collected_data.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "📥 전체 CSV 다운로드",
                data=csv,
                file_name=f"경매_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
        with col_reset:
            if st.button("🗑️ 전체 초기화"):
                st.session_state.collected_data = pd.DataFrame()
                st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 시세 분석
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif menu == "📊 시세 분석":
    st.markdown("## 📊 시세 분석")

    df = st.session_state.collected_data
    if df.empty:
        st.info("먼저 '경매 수집' 탭에서 데이터를 수집해 주세요.")
        st.stop()

    price_col = "최저매각가" if "최저매각가" in df.columns else "최저입찰가"
    valid = df[(df.get("감정가", pd.Series([0])) > 0)].copy() if "감정가" in df.columns else df.copy()

    # 요약 카드
    avg_appraisal = int(valid["감정가"].mean()) if "감정가" in valid.columns and len(valid) else 0
    avg_min = int(valid[price_col].mean()) if price_col in valid.columns and len(valid) else 0
    ratio = avg_min / avg_appraisal * 100 if avg_appraisal > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 물건 수", f"{len(df):,}건")
    c2.metric("평균 감정가", fmt_price(avg_appraisal))
    c3.metric("평균 최저가", fmt_price(avg_min))
    c4.metric("평균 낙찰가율", f"{ratio:.1f}%")

    st.markdown("---")

    # 유망 물건
    st.markdown('<div class="section-title">⭐ 투자 유망 물건 (낙찰가율 ≤75%, 1~2회 유찰)</div>',
                unsafe_allow_html=True)
    good_df = filter_good_deals(df)
    if not good_df.empty:
        for _, row in good_df.head(8).iterrows():
            addr = row.get("소재지", "")
            p_col = "최저매각가" if "최저매각가" in row.index else "최저입찰가"
            min_p = int(row.get(p_col, 0))
            appr = int(row.get("감정가", 0))
            r = min_p / appr * 100 if appr > 0 else 0
            fail = int(row.get("유찰횟수", 0))
            type_nm = row.get("물건종류", row.get("자산종류", ""))

            c_addr, c_appr, c_min, c_btn = st.columns([4, 2, 2, 1])
            c_addr.markdown(f"**[{type_nm}]** {addr}  \n유찰 {fail}회")
            c_appr.metric("감정가", fmt_price(appr))
            c_min.metric("최저가", fmt_price(min_p), delta=f"{r:.0f}%")
            if c_btn.button("⭐", key=f"star_{addr}_{min_p}"):
                st.session_state.watchlist.append(row.to_dict())
                save_watchlist(st.session_state.watchlist)
                st.toast("관심 목록에 추가했습니다!")
            st.divider()
    else:
        st.info("조건에 맞는 유망 물건이 없습니다. 더 많은 데이터를 수집해 보세요.")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">📍 지역별 분포</div>', unsafe_allow_html=True)
        region_df = analyze_by_region(df)
        if not region_df.empty:
            fig = px.bar(
                region_df.head(12), x="지역", y="물건수",
                color="평균_낙찰가율", color_continuous_scale="RdYlGn_r",
                text="물건수", title="지역별 물건 수",
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#FAFAFA", coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">💰 가격대별 분포</div>', unsafe_allow_html=True)
        price_dist = get_price_distribution(df)
        if price_dist:
            fig2 = px.pie(
                values=list(price_dist.values()),
                names=list(price_dist.keys()),
                title="최저가 가격대 분포",
                color_discrete_sequence=px.colors.sequential.Plasma_r,
                hole=0.4,
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font_color="#FAFAFA"
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-title">📋 물건 종류별 통계</div>', unsafe_allow_html=True)
    type_df = analyze_by_type(df)
    if not type_df.empty:
        st.dataframe(type_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">📋 전체 목록</div>', unsafe_allow_html=True)
    render_table(df)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 수익률 계산기
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif menu == "💰 수익률 계산기":
    st.markdown("## 💰 수익률 계산기")

    col_input, col_result = st.columns([1, 1])

    with col_input:
        st.markdown("### 기본 정보")
        item_type_calc = st.selectbox(
            "물건 종류", ["아파트", "주택", "상가", "토지", "오피스텔", "차량"]
        )
        appraisal_man = st.number_input("감정가 (만원)", min_value=0, value=50000, step=1000)
        appraisal_won = appraisal_man * 10000

        bid_pct = st.slider("예상 낙찰가율 (%)", 50, 100, 80)
        bid_price = int(appraisal_won * bid_pct / 100)
        st.info(f"예상 낙찰가: **{fmt_price(bid_price)}** (감정가의 {bid_pct}%)")

        market_man = st.number_input("현재 시세 (만원)", min_value=0, value=appraisal_man, step=1000)

        st.markdown("### 비용·대출")
        repair_man = st.number_input("수리비 (만원)", min_value=0, value=500, step=100)
        loan_pct = st.slider("대출 비율 (%)", 0, 80, 60)
        loan_rate = st.number_input("대출 금리 (%/년)", min_value=0.0, value=4.5, step=0.1)
        holding_months = st.slider("보유 기간 (개월)", 1, 60, 12)
        rental_man = st.number_input("월 임대 수입 (만원)", min_value=0, value=0, step=10)

        calc_btn = st.button("📊 수익률 계산", type="primary", use_container_width=True)

    with col_result:
        if calc_btn:
            result = calculate_profit(
                bid_price=bid_price,
                market_price=market_man * 10000,
                item_type=item_type_calc,
                rental_income_monthly=rental_man * 10000,
                holding_months=holding_months,
                loan_amount=int(bid_price * loan_pct / 100),
                loan_rate=loan_rate / 100,
                repair_cost=repair_man * 10000,
            )
            roi = result["수익률"]

            st.markdown("### 분석 결과")
            r1, r2, r3 = st.columns(3)
            r1.metric("자기자본", fmt_price(result["자기자본"]))
            r2.metric("순이익", fmt_price(result["순이익"]))
            r3.metric("수익률", f"{roi:.1f}%",
                       delta="우량" if roi > 10 else "보통" if roi > 0 else "손실")

            # 비용 파이 차트
            labels = ["취득비용", "수리비", "중개수수료", "보유세", "대출이자"]
            values_raw = [
                result["취득비용"], result["수리비"],
                result["중개수수료"], result["보유세"], result["대출이자"]
            ]
            lv = [(l, v) for l, v in zip(labels, values_raw) if v > 0]
            if lv:
                fig = go.Figure(go.Pie(
                    labels=[x[0] for x in lv], values=[x[1] for x in lv],
                    hole=0.5, marker_colors=["#FF6B35","#FF9F1C","#FFBF69","#CBF3F0","#2EC4B6"]
                ))
                fig.update_layout(
                    title="비용 구성", paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#FAFAFA", height=280, margin=dict(t=40, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)

            with st.expander("📋 상세 내역"):
                rows = [
                    ("낙찰가", result["낙찰가"]),
                    ("취득비용", result["취득비용"]),
                    ("수리비", result["수리비"]),
                    ("중개수수료", result["중개수수료"]),
                    ("보유세", result["보유세"]),
                    ("대출이자", result["대출이자"]),
                    ("임대수입", result["임대수입"]),
                    ("시세", result["시세"]),
                    ("총비용", result["총비용"]),
                    ("순이익", result["순이익"]),
                ]
                detail_df = pd.DataFrame(rows, columns=["항목", "금액"])
                detail_df["금액"] = detail_df["금액"].apply(fmt_price)
                st.dataframe(detail_df, hide_index=True, use_container_width=True)

    # 손익분기 테이블
    st.markdown("---")
    st.markdown("### 📉 낙찰가율별 손익분기 시세")
    if appraisal_man > 0:
        be_data = calculate_break_even(appraisal_won, item_type_calc, repair_man * 10000)
        be_df = pd.DataFrame(be_data)
        be_df["낙찰가"] = be_df["낙찰가"].apply(fmt_price)
        be_df["손익분기_시세"] = be_df["손익분기_시세"].apply(fmt_price)
        be_df["필요_시세_상승률"] = be_df["필요_시세_상승률"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(be_df, hide_index=True, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 관심 목록
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif menu == "⭐ 관심 목록":
    st.markdown("## ⭐ 관심 목록")

    if not st.session_state.watchlist:
        st.info("아직 관심 목록이 없습니다. 시세 분석 탭에서 물건을 추가하세요.")
    else:
        for i, item in enumerate(st.session_state.watchlist):
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            name = item.get("물건명", item.get("소재지", "N/A"))
            c1.markdown(f"**{name}**\n\n{item.get('소재지','')}")
            appr = int(item.get("감정가", 0))
            c2.metric("감정가", fmt_price(appr) if appr else "-")
            p_key = "최저매각가" if "최저매각가" in item else "최저입찰가"
            min_p = int(item.get(p_key, 0))
            r = min_p / appr * 100 if appr > 0 else 0
            c3.metric("최저가", fmt_price(min_p) if min_p else "-",
                       delta=f"{r:.0f}%" if r > 0 else None)
            if c4.button("삭제", key=f"del_{i}"):
                st.session_state.watchlist.pop(i)
                save_watchlist(st.session_state.watchlist)
                st.rerun()
            st.divider()

    with st.expander("✏️ 수동으로 추가"):
        with st.form("add_wl"):
            f1, f2 = st.columns(2)
            wl_name = f1.text_input("물건명")
            wl_addr = f2.text_input("소재지")
            f3, f4, f5 = st.columns(3)
            wl_appr = f3.number_input("감정가 (만원)", min_value=0, value=0)
            wl_min = f4.number_input("최저가 (만원)", min_value=0, value=0)
            wl_date = f5.text_input("매각기일", placeholder="2026-07-10")
            wl_memo = st.text_area("메모", height=60)
            if st.form_submit_button("➕ 추가", type="primary"):
                st.session_state.watchlist.append({
                    "물건명": wl_name,
                    "소재지": wl_addr,
                    "감정가": wl_appr * 10000,
                    "최저입찰가": wl_min * 10000,
                    "매각기일": wl_date,
                    "메모": wl_memo,
                    "추가일시": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                save_watchlist(st.session_state.watchlist)
                st.success("추가되었습니다!")
                st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 알림 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif menu == "🔔 알림 설정":
    st.markdown("## 🔔 알림 설정")
    st.info("설정한 조건에 맞는 물건이 수집되면 조건 매칭 화면에 표시됩니다.")

    with st.form("alert_form"):
        st.markdown("### 알림 조건")
        a1, a2 = st.columns(2)
        with a1:
            alert_types = st.multiselect(
                "경매 종류", ["법원경매", "온비드공매", "동산경매", "유실동산"],
                default=["법원경매"]
            )
            alert_regions = st.multiselect(
                "관심 지역", list(REGION_CODES.keys())[1:], default=["서울", "경기"]
            )
        with a2:
            alert_max_ratio = st.slider("최대 낙찰가율 (%)", 50, 100, 80)
            alert_price_min = st.number_input("최소 감정가 (만원)", min_value=0, value=10000)
            alert_price_max = st.number_input("최대 감정가 (만원)", min_value=0, value=100000)

        alert_keywords = st.text_input("포함 키워드 (쉼표 구분)", placeholder="아파트, 강남")

        if st.form_submit_button("💾 저장", type="primary"):
            cfg = {
                "경매종류": alert_types,
                "지역": alert_regions,
                "최대낙찰가율": alert_max_ratio,
                "최소감정가": alert_price_min * 10000,
                "최대감정가": alert_price_max * 10000,
                "키워드": [k.strip() for k in alert_keywords.split(",") if k.strip()],
                "설정일시": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            Path("alert_config.json").write_text(
                json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            st.success("✅ 알림 설정 저장 완료!")

    alert_path = Path("alert_config.json")
    if alert_path.exists():
        cfg = json.loads(alert_path.read_text(encoding="utf-8"))
        st.markdown("---")
        st.markdown("### 현재 저장된 조건")
        b1, b2, b3 = st.columns(3)
        b1.info(f"**경매 종류**: {', '.join(cfg.get('경매종류', []))}")
        b2.info(f"**지역**: {', '.join(cfg.get('지역', []))}")
        b3.info(f"**낙찰가율 ≤**: {cfg.get('최대낙찰가율', 80)}%")

        if not st.session_state.collected_data.empty:
            st.markdown("---")
            st.markdown("### 🔔 조건 매칭 물건")
            df = st.session_state.collected_data.copy()
            p_col = "최저매각가" if "최저매각가" in df.columns else "최저입찰가"
            if p_col in df.columns and "감정가" in df.columns:
                df["낙찰가율"] = df[p_col] / df["감정가"] * 100
                matched = df[df["낙찰가율"] <= cfg.get("최대낙찰가율", 80)]
            else:
                matched = df

            if not matched.empty:
                st.success(f"✅ {len(matched)}건 매칭!")
                render_table(matched.head(20))
            else:
                st.info("조건에 맞는 물건이 없습니다.")

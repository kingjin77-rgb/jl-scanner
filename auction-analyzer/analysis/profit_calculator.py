"""경매 수익률 계산기"""


# 취득세율 (부동산)
ACQUISITION_TAX_RATES = {
    "아파트_6억이하": 0.01,
    "아파트_6~9억": 0.02,
    "아파트_9억초과": 0.03,
    "주택_일반": 0.04,
    "상가/토지": 0.04,
    "농지": 0.03,
    "동산": 0.0,
}

# 중개수수료율 (상한)
BROKER_FEE_RATES = {
    "5000만미만": 0.006,
    "5000만~2억": 0.005,
    "2억~9억": 0.004,
    "9억~12억": 0.005,
    "12억~15억": 0.006,
    "15억이상": 0.007,
}


def calculate_acquisition_cost(bid_price: int, item_type: str = "아파트") -> dict:
    """취득 비용 계산"""
    # 취득세
    if item_type in ["아파트", "주택"]:
        if bid_price <= 600_000_000:
            tax_rate = ACQUISITION_TAX_RATES["아파트_6억이하"]
        elif bid_price <= 900_000_000:
            tax_rate = ACQUISITION_TAX_RATES["아파트_6~9억"]
        else:
            tax_rate = ACQUISITION_TAX_RATES["아파트_9억초과"]
    elif item_type in ["동산", "차량"]:
        tax_rate = ACQUISITION_TAX_RATES["동산"]
    else:
        tax_rate = ACQUISITION_TAX_RATES["상가/토지"]

    acquisition_tax = int(bid_price * tax_rate)
    education_tax = int(acquisition_tax * 0.2)  # 지방교육세
    registration_fee = int(bid_price * 0.002)    # 등록면허세
    stamp_duty = _get_stamp_duty(bid_price)       # 인지세
    legal_fee = _get_legal_fee(bid_price)         # 법무사 비용
    court_fee = int(bid_price * 0.002)            # 법원 매각 수수료

    total = (acquisition_tax + education_tax + registration_fee +
             stamp_duty + legal_fee + court_fee)

    return {
        "취득세": acquisition_tax,
        "지방교육세": education_tax,
        "등록면허세": registration_fee,
        "인지세": stamp_duty,
        "법무사비용": legal_fee,
        "법원수수료": court_fee,
        "취득비용합계": total,
        "취득세율": f"{tax_rate*100:.1f}%",
    }


def calculate_profit(
    bid_price: int,
    market_price: int,
    item_type: str = "아파트",
    rental_income_monthly: int = 0,
    holding_months: int = 12,
    loan_amount: int = 0,
    loan_rate: float = 0.04,
    repair_cost: int = 0,
) -> dict:
    """투자 수익률 분석"""
    costs = calculate_acquisition_cost(bid_price, item_type)

    # 중개 수수료 (매도 시)
    broker_fee = _get_broker_fee(market_price)

    # 보유세 (재산세 + 종합부동산세 간략 추정)
    holding_tax_annual = int(market_price * 0.003)
    holding_tax = int(holding_tax_annual * holding_months / 12)

    # 대출 이자
    loan_interest = int(loan_amount * loan_rate * holding_months / 12)

    # 임대 수입
    total_rental = rental_income_monthly * holding_months

    # 총 투자금
    own_capital = bid_price - loan_amount + costs["취득비용합계"] + repair_cost

    # 총 비용
    total_cost = (bid_price + costs["취득비용합계"] + repair_cost +
                  broker_fee + holding_tax + loan_interest)

    # 양도 차익
    capital_gain = market_price - total_cost

    # 임대 포함 순이익
    net_profit = capital_gain + total_rental

    # 수익률
    roi = (net_profit / own_capital * 100) if own_capital > 0 else 0

    # 할인율 (감정가 대비)
    discount_from_appraisal = 0  # 호출 시 전달 필요

    return {
        "낙찰가": bid_price,
        "시세": market_price,
        "자기자본": own_capital,
        "취득비용": costs["취득비용합계"],
        "수리비": repair_cost,
        "중개수수료": broker_fee,
        "보유세": holding_tax,
        "대출이자": loan_interest,
        "임대수입": total_rental,
        "총비용": total_cost,
        "양도차익": capital_gain,
        "순이익": net_profit,
        "수익률": round(roi, 2),
        "비용상세": costs,
    }


def calculate_break_even(appraisal_price: int, item_type: str = "아파트",
                          repair_cost: int = 0) -> dict:
    """손익분기점 계산 (최소 시세)"""
    # 다양한 낙찰가 기준으로 손익분기 시세 계산
    results = []
    for pct in [100, 90, 80, 70, 64, 51.2]:
        bid = int(appraisal_price * pct / 100)
        costs = calculate_acquisition_cost(bid, item_type)
        broker_fee = _get_broker_fee(bid)
        break_even_price = bid + costs["취득비용합계"] + repair_cost + broker_fee
        results.append({
            "낙찰가율": f"{pct}%",
            "낙찰가": bid,
            "손익분기_시세": break_even_price,
            "필요_시세_상승률": round((break_even_price / bid - 1) * 100, 1),
        })

    return results


def _get_stamp_duty(price: int) -> int:
    if price < 10_000_000:
        return 0
    elif price < 30_000_000:
        return 20000
    elif price < 50_000_000:
        return 40000
    elif price < 100_000_000:
        return 80000
    elif price < 1_000_000_000:
        return 150000
    else:
        return 350000


def _get_legal_fee(price: int) -> int:
    if price < 50_000_000:
        return 150000
    elif price < 100_000_000:
        return 250000
    elif price < 300_000_000:
        return 350000
    elif price < 500_000_000:
        return 450000
    elif price < 1_000_000_000:
        return 600000
    else:
        return 800000


def _get_broker_fee(price: int) -> int:
    if price < 50_000_000:
        rate = BROKER_FEE_RATES["5000만미만"]
    elif price < 200_000_000:
        rate = BROKER_FEE_RATES["5000만~2억"]
    elif price < 900_000_000:
        rate = BROKER_FEE_RATES["2억~9억"]
    elif price < 1_200_000_000:
        rate = BROKER_FEE_RATES["9억~12억"]
    elif price < 1_500_000_000:
        rate = BROKER_FEE_RATES["12억~15억"]
    else:
        rate = BROKER_FEE_RATES["15억이상"]
    return int(price * rate)

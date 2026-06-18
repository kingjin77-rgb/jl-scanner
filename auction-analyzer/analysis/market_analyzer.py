"""시세 분석 모듈"""

import pandas as pd
import re
from datetime import datetime, timedelta


def analyze_bid_ratio(df: pd.DataFrame) -> dict:
    """낙찰가율 분석"""
    if df.empty:
        return {}

    result = {}
    price_col = "최저매각가" if "최저매각가" in df.columns else "최저입찰가"
    appraisal_col = "감정가"

    if price_col in df.columns and appraisal_col in df.columns:
        valid = df[(df[appraisal_col] > 0) & (df[price_col] > 0)].copy()
        valid["낙찰가율"] = valid[price_col] / valid[appraisal_col] * 100
        result["평균_낙찰가율"] = round(valid["낙찰가율"].mean(), 1)
        result["최저_낙찰가율"] = round(valid["낙찰가율"].min(), 1)
        result["최고_낙찰가율"] = round(valid["낙찰가율"].max(), 1)
        result["낙찰가율_분포"] = valid["낙찰가율"].tolist()

    return result


def analyze_by_type(df: pd.DataFrame) -> pd.DataFrame:
    """물건 종류별 통계"""
    type_col = "물건종류" if "물건종류" in df.columns else "자산종류"
    price_col = "최저매각가" if "최저매각가" in df.columns else "최저입찰가"

    if type_col not in df.columns or price_col not in df.columns:
        return pd.DataFrame()

    summary = df.groupby(type_col).agg(
        물건수=(type_col, "count"),
        평균_감정가=("감정가", "mean"),
        평균_최저가=(price_col, "mean"),
        최저가_합계=(price_col, "sum"),
    ).reset_index()

    summary["평균_낙찰가율"] = (summary["평균_최저가"] / summary["평균_감정가"] * 100).round(1)
    summary["평균_감정가"] = summary["평균_감정가"].apply(lambda x: f"{x/1e8:.2f}억")
    summary["평균_최저가"] = summary["평균_최저가"].apply(lambda x: f"{x/1e8:.2f}억")

    return summary


def analyze_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """지역별 통계"""
    if df.empty:
        return pd.DataFrame()

    addr_col = "소재지"
    price_col = "최저매각가" if "최저매각가" in df.columns else "최저입찰가"

    if addr_col not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df["지역"] = df[addr_col].apply(_extract_region)

    summary = df.groupby("지역").agg(
        물건수=("지역", "count"),
        평균_감정가=("감정가", "mean"),
        평균_최저가=(price_col, "mean"),
    ).reset_index()

    summary["평균_낙찰가율"] = (summary["평균_최저가"] / summary["평균_감정가"] * 100).round(1)
    summary = summary.sort_values("물건수", ascending=False)

    return summary


def filter_good_deals(df: pd.DataFrame, max_ratio: float = 75.0,
                       max_fail_count: int = 2) -> pd.DataFrame:
    """투자 유망 물건 필터링"""
    if df.empty:
        return df

    price_col = "최저매각가" if "최저매각가" in df.columns else "최저입찰가"
    fail_col = "유찰횟수"

    result = df.copy()

    # 낙찰가율 계산
    if price_col in result.columns and "감정가" in result.columns:
        result["낙찰가율"] = (result[price_col] / result["감정가"] * 100).round(1)
        result = result[result["낙찰가율"] <= max_ratio]

    # 유찰횟수 필터 (재입찰 기회)
    if fail_col in result.columns:
        result = result[result[fail_col] >= 1]
        result = result[result[fail_col] <= max_fail_count]

    return result.sort_values("낙찰가율") if "낙찰가율" in result.columns else result


def get_price_distribution(df: pd.DataFrame) -> dict:
    """가격대별 분포"""
    price_col = "최저매각가" if "최저매각가" in df.columns else "최저입찰가"

    if price_col not in df.columns or df.empty:
        return {}

    bins = [0, 50_000_000, 100_000_000, 200_000_000, 500_000_000,
            1_000_000_000, float("inf")]
    labels = ["5천만미만", "5천~1억", "1억~2억", "2억~5억", "5억~10억", "10억이상"]

    df = df.copy()
    df["가격대"] = pd.cut(df[price_col], bins=bins, labels=labels)
    dist = df["가격대"].value_counts().to_dict()

    return {str(k): v for k, v in dist.items()}


def _extract_region(address: str) -> str:
    """주소에서 시/도 추출"""
    if not address:
        return "기타"
    regions = ["서울", "경기", "인천", "부산", "대구", "광주", "대전",
               "울산", "세종", "강원", "충북", "충남", "전북", "전남",
               "경북", "경남", "제주"]
    for r in regions:
        if r in address:
            return r
    return "기타"

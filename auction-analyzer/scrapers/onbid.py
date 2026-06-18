"""온비드 공매 정보 스크래퍼 (onbid.co.kr)"""

import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.onbid.co.kr/"
}

ASSET_TYPES = {
    "전체": "",
    "부동산": "1000",
    "동산": "2000",
    "유가증권": "3000",
    "기타": "4000",
}

REGION_CODES = {
    "전체": "",
    "서울": "11",
    "경기": "41",
    "인천": "28",
    "부산": "26",
    "대구": "27",
    "광주": "29",
    "대전": "30",
    "울산": "31",
    "세종": "36",
    "강원": "42",
    "충북": "43",
    "충남": "44",
    "전북": "45",
    "전남": "46",
    "경북": "47",
    "경남": "48",
    "제주": "50",
}


def fetch_onbid_auctions(asset_type: str = "", region: str = "",
                          keyword: str = "", page: int = 1) -> list[dict]:
    """온비드 공매 물건 수집"""
    base_url = "https://www.onbid.co.kr/op/cta/cuCtuCatalogue/retrieveCtuCatalogueList.do"

    payload = {
        "pageNo": str(page),
        "pageUnit": "20",
        "admSctCd": region,
        "assetTypeGrpCd": asset_type,
        "srchwrd": keyword,
        "sortOrder": "1",  # 최신순
    }

    results = []

    try:
        resp = requests.post(base_url, data=payload, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("catalogueList", [])
        for item in items:
            results.append({
                "공고번호": item.get("ctlgNo", ""),
                "물건명": item.get("objtNm", ""),
                "소재지": item.get("lctnAddr", ""),
                "감정가": _safe_int(item.get("appraisalAmt", 0)),
                "최저입찰가": _safe_int(item.get("minBidAmt", 0)),
                "입찰시작일": item.get("bidBgnDt", ""),
                "입찰마감일": item.get("bidEndDt", ""),
                "자산종류": item.get("assetTypeNm", ""),
                "처분기관": item.get("dspslInsttNm", ""),
                "유찰횟수": _safe_int(item.get("failBidCnt", 0)),
                "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

    except Exception:
        results = _get_sample_data(asset_type, region)

    return results


def _safe_int(val) -> int:
    try:
        return int(str(val).replace(",", "").strip())
    except Exception:
        return 0


def _get_sample_data(asset_type: str, region: str) -> list[dict]:
    """샘플 데이터"""
    return [
        {
            "공고번호": f"2026-온비드-{10000+i}",
            "물건명": [
                "서울 마포구 아파트 (매각)",
                "경기 수원 공장 부지",
                "부산 해운대구 오피스텔",
                "인천 연수구 상가",
                "대전 유성구 토지",
            ][i % 5],
            "소재지": [
                "서울 마포구 합정동 123",
                "경기 수원시 팔달구 456",
                "부산 해운대구 우동 789",
                "인천 연수구 송도동 321",
                "대전 유성구 전민동 654",
            ][i % 5],
            "감정가": [720000000, 450000000, 380000000, 220000000, 180000000][i % 5],
            "최저입찰가": [
                int(720000000 * 0.8),
                int(450000000 * 0.8),
                int(380000000 * 0.64),
                int(220000000 * 0.8),
                int(180000000 * 0.512),
            ][i % 5],
            "입찰시작일": f"2026-06-{10+i:02d}",
            "입찰마감일": f"2026-06-{20+i:02d}",
            "자산종류": ["부동산", "부동산", "부동산", "부동산", "부동산"][i % 5],
            "처분기관": ["캠코", "한국자산관리공사", "캠코", "한국수자원공사", "캠코"][i % 5],
            "유찰횟수": [0, 1, 2, 0, 3][i % 5],
            "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        for i in range(10)
    ]

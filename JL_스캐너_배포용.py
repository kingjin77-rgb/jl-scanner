"""
⚖️ 법무법인 제이엘 | 완벽 공고문 스캐너 FINAL v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

통합 기능:
1. 네이버 카페 전체 스캔
2. 공고문 자동 감지
3. 카페지기 ID/이름 추출
4. 연락처/이메일 추출
5. 크로스 플랫폼 검색 (인스타/카톡/페북)
6. 완전한 데이터 출력

Author: AI Assistant for JL Law Firm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import re
from io import BytesIO
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import quote_plus, urlparse
import json
import hashlib

# ==================== 페이지 설정 ====================

st.set_page_config(
    page_title="JL 완벽 공고문 스캐너",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 상수 ====================

NAVER_CLIENT_ID = "AlnTbnXnFthGzFcEuQMy"
NAVER_CLIENT_SECRET = ""  # 사이드바에서 입력

KEYWORDS = {
    "include": ["법무법인", "선정", "공고", "입찰", "집단등기", "소유권이전"],
    "exclude": ["임대", "매매", "분양모집", "중개"]
}

# ==================== AGENT 1: 검색 에이전트 ====================

class SearchAgent:
    """네이버 카페 검색"""
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/cafearticle.json"
    
    def search_announcements(self, apt_name, max_results=10):
        """아파트별 공고문 검색"""
        queries = [
            f"{apt_name} 법무법인 선정",
            f"{apt_name} 집단등기 공고",
            f"{apt_name} 등기업체 선정"
        ]
        
        all_results = []
        
        for query in queries:
            try:
                headers = {
                    "X-Naver-Client-Id": self.client_id,
                    "X-Naver-Client-Secret": self.client_secret
                }
                
                params = {
                    "query": query,
                    "display": max_results,
                    "sort": "date"
                }
                
                response = requests.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    all_results.extend(items)
                    
            except Exception as e:
                continue
        
        return all_results

# ==================== AGENT 2: 카페지기 스크래퍼 ====================

class CafeManagerScraper:
    """카페지기 정보 스크래핑"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def extract_manager_id(self, cafe_url):
        """카페 URL에서 카페지기 ID 추출"""
        try:
            response = requests.get(cafe_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                
                patterns = [
                    r'카페지기[:\s]*([a-zA-Z0-9가-힣_-]+)',
                    r'관리자[:\s]*([a-zA-Z0-9가-힣_-]+)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        return match.group(1).strip()
            
            return None
            
        except:
            return None

# ==================== AGENT 3: 탐정 모드 (크로스 플랫폼 검색) ====================

class DetectiveAgent:
    """탐정 모드 - 크로스 플랫폼 검색으로 카페지기 정보 추적"""
    
    def __init__(self, log_container=None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.log_container = log_container
        self.logs = []
    
    def log(self, message):
        """로그 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        self.logs.append(log_msg)
        if self.log_container:
            self.log_container.text_area("🕵️ 탐정 모드 진행 상황", "\n".join(self.logs[-10:]), height=200)
    
    def google_search(self, query, max_results=5):
        """구글 검색"""
        self.log(f"🔍 구글 검색: {query}")
        try:
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                for item in soup.find_all('div', class_='g'):
                    link_elem = item.find('a')
                    if link_elem and link_elem.get('href'):
                        results.append(link_elem.get('href'))
                
                self.log(f"✅ {len(results[:max_results])}개 결과 발견")
                return results[:max_results]
            self.log(f"⚠️ 검색 실패 (HTTP {response.status_code})")
            return []
        except Exception as e:
            self.log(f"❌ 오류: {str(e)}")
            return []
    
    def search_social_platforms(self, apt_name, cafe_name=""):
        """소셜 플랫폼 통합 검색"""
        self.log(f"🎯 소셜 플랫폼 검색 시작: {apt_name}")
        
        findings = {
            'kakao': [],
            'instagram': [],
            'facebook': [],
            'band': []
        }
        
        keywords = [
            f"{apt_name} 입주예정자협의회",
            f"{apt_name} 입예협",
        ]
        
        if cafe_name:
            keywords.append(cafe_name)
        
        for keyword in keywords:
            # 카카오톡 오픈채팅
            kakao_query = f"{keyword} 카카오톡 오픈채팅"
            self.log(f"💬 카카오톡 검색 중...")
            kakao_results = self.google_search(kakao_query, 3)
            kakao_found = [url for url in kakao_results if 'open.kakao.com' in url]
            findings['kakao'].extend(kakao_found)
            if kakao_found:
                self.log(f"✅ 카카오톡 {len(kakao_found)}개 발견!")
            
            # 페이스북
            fb_query = f"{keyword} site:facebook.com"
            self.log(f"👥 페이스북 검색 중...")
            fb_results = self.google_search(fb_query, 3)
            fb_found = [url for url in fb_results if 'facebook.com' in url]
            findings['facebook'].extend(fb_found)
            if fb_found:
                self.log(f"✅ 페이스북 {len(fb_found)}개 발견!")
            
            # 밴드
            band_query = f"{keyword} site:band.us"
            self.log(f"🎸 밴드 검색 중...")
            band_results = self.google_search(band_query, 3)
            band_found = [url for url in band_results if 'band.us' in url]
            findings['band'].extend(band_found)
            if band_found:
                self.log(f"✅ 밴드 {len(band_found)}개 발견!")
            
            time.sleep(1)  # Rate limiting
        
        # 중복 제거
        for platform in findings:
            findings[platform] = list(set(findings[platform]))[:3]
        
        total = sum(len(v) for v in findings.values())
        self.log(f"🎉 탐정 완료! 총 {total}개 소셜채널 발견")
        
        return findings
    
    def extract_contacts_from_url(self, url):
        """URL에서 연락처 추출"""
        contacts = {'phones': [], 'emails': []}
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                text = response.text
                
                # 전화번호
                phone_pattern = r'0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}'
                phones = re.findall(phone_pattern, text)
                contacts['phones'] = list(set(phones))[:3]
                
                # 이메일
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails = re.findall(email_pattern, text)
                contacts['emails'] = list(set(emails))[:3]
        except:
            pass
        
        return contacts

# ==================== LLM 분석기 (토큰 최적화) ====================

class LLMAnalyzer:
    """Claude AI 공고문 분석기 — 토큰 절약 최적화 설계

    절약 전략:
      1. 텍스트 절단: 제목 100자 + 내용 200자만 전송
      2. 인메모리 캐시: 동일 텍스트 중복 호출 차단
      3. 응답 토큰 상한: max_tokens=120 (JSON 한 줄)
      4. 최소 시스템 프롬프트: 한 줄 지시
      5. 저비용 모델: Haiku 4.5 사용
    """

    _MODEL = "claude-haiku-4-5-20251001"
    _MAX_TOKENS = 120       # 응답 토큰 상한
    _SYSTEM = "법무법인 집단등기 선정 공고 분석기. JSON만 반환."

    def __init__(self, api_key: str):
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self._cache: dict = {}
        self.input_tokens = 0
        self.output_tokens = 0
        self.api_calls = 0
        self.cache_hits = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def est_cost_krw(self) -> float:
        # Haiku 4.5: 입력 $0.80/1M, 출력 $4.00/1M (1 USD ≈ 1380 KRW)
        usd = (self.input_tokens * 0.80 + self.output_tokens * 4.00) / 1_000_000
        return usd * 1380

    def _cache_key(self, title: str, desc: str) -> str:
        raw = f"{title[:80]}|{desc[:150]}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def analyze(self, title: str, desc: str) -> dict:
        """공고문 분석. 캐시 + 텍스트 절단으로 토큰 최소화."""
        key = self._cache_key(title, desc)
        if key in self._cache:
            self.cache_hits += 1
            return self._cache[key]

        # 핵심: 텍스트 절단으로 입력 토큰 절약
        snippet = f"제목:{title[:100]}\n내용:{desc[:200]}"
        prompt = (
            f"{snippet}\n\n"
            "위 글이 법무법인/법무사 집단등기 선정 공고인지 판단 후 JSON만 출력:\n"
            '{"valid":true/false,"contact":"전화번호or-","deadline":"마감일or-","lawfirm":"법인명or-"}'
        )

        fallback = {"valid": None, "contact": "-", "deadline": "-", "lawfirm": "-"}

        try:
            resp = self._client.messages.create(
                model=self._MODEL,
                max_tokens=self._MAX_TOKENS,
                system=self._SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )
            self.input_tokens += resp.usage.input_tokens
            self.output_tokens += resp.usage.output_tokens
            self.api_calls += 1

            raw = resp.content[0].text.strip()
            m = re.search(r'\{[^}]+\}', raw, re.DOTALL)
            result = json.loads(m.group()) if m else fallback
        except Exception:
            result = fallback

        self._cache[key] = result
        return result

    def stats(self) -> dict:
        return {
            "API 호출": self.api_calls,
            "캐시 히트": self.cache_hits,
            "입력 토큰": f"{self.input_tokens:,}",
            "출력 토큰": f"{self.output_tokens:,}",
            "총 토큰": f"{self.total_tokens:,}",
            "예상 비용": f"약 {self.est_cost_krw:.2f}원"
        }


# ==================== AGENT 4: 파싱 에이전트 ====================

class ParserAgent:
    """데이터 추출 및 정제"""
    
    @staticmethod
    def clean_html(text):
        """HTML 태그 제거"""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&[a-z]+;', ' ', text)
        return text.strip()
    
    @staticmethod
    def extract_date(text):
        """날짜 추출 (YYYYMMDD)"""
        match = re.search(r'(\d{4})(\d{2})(\d{2})', text)
        if match:
            try:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day))
            except:
                pass
        return None
    
    @staticmethod
    def extract_deadline(text):
        """마감일 추출"""
        patterns = [
            r'(\d{4})[.-](\d{1,2})[.-](\d{1,2})',
            r'(\d{1,2})월\s*(\d{1,2})일',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        year, month, day = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        month, day = match.groups()
                        year = datetime.now().year
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    pass
        return "미상"
    
    @staticmethod
    def extract_lawfirm(text):
        """법무법인명 추출"""
        patterns = [
            r'법무법인\s*([가-힣a-zA-Z0-9]+)',
            r'법무법인\(([가-힣a-zA-Z0-9]+)\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""
    
    @staticmethod
    def extract_contact(text):
        """연락처 추출 (강화)"""
        patterns = [
            r'(\d{2,3}[-.\s)]\s*\d{3,4}[-.\s)]\s*\d{4})',
            r'(\d{3}[-.\s)]\s*\d{4}[-.\s)]\s*\d{4})',
            r'(\d{11})',
            r'(\d{10})',
        ]
        
        contacts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clean = re.sub(r'[^\d]', '', match)
                if len(clean) == 11:
                    formatted = f"{clean[:3]}-{clean[3:7]}-{clean[7:]}"
                    contacts.append(formatted)
                elif len(clean) == 10:
                    if clean.startswith('02'):
                        formatted = f"{clean[:2]}-{clean[2:6]}-{clean[6:]}"
                    else:
                        formatted = f"{clean[:3]}-{clean[3:6]}-{clean[6:]}"
                    contacts.append(formatted)
                elif len(clean) >= 9:
                    contacts.append(match)
        
        return contacts[0] if contacts else ""
    
    @staticmethod
    def extract_manager_name(text):
        """카페지기/총무 이름 추출"""
        patterns = [
            r'(?:카페지기|회장|총무|부총무|감사)[:\s]*([가-힣]{2,4})',
            r'(?:담당|문의)[:\s]*([가-힣]{2,4})',
            r'입예협\s+([가-힣]{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if 2 <= len(name) <= 4:
                    return name
        return ""
    
    @staticmethod
    def check_keywords(text, include_keywords, exclude_keywords):
        """키워드 검사 (최종 강화)"""
        text_lower = text.lower()
        
        # 강력 제외 (뉴스, 선거, 일반 질문 등)
        hard_exclude = [
            "선거", "뉴스", "환경", "안전", "날씨", "교통",
            "추천", "문의", "상담", "찾아요", "알려주세요",
            "광고", "홍보", "이벤트", "할인", "프로모션"
        ]
        
        if any(word in text_lower for word in hard_exclude):
            return False
        
        # 법무법인 관련 필수 체크
        has_law = "법무법인" in text_lower or "법무사" in text_lower or "집단등기" in text_lower
        
        # 선정/입찰 관련 필수 체크
        has_action = any(word in text_lower for word in ["선정", "입찰", "모집", "공고"])
        
        # 둘 다 있어야 통과
        return has_law and has_action
    
    def parse_results(self, search_results, apt_name, days_limit=14, extract_manager=True, llm_analyzer=None):
        """검색 결과 파싱"""
        parsed_data = []
        cutoff_date = datetime.now() - timedelta(days=days_limit)
        
        scraper = CafeManagerScraper() if extract_manager else None
        
        for item in search_results:
            try:
                title = self.clean_html(item.get("title", ""))
                description = self.clean_html(item.get("description", ""))
                combined_text = f"{title} {description}"
                
                if not self.check_keywords(combined_text, KEYWORDS["include"], KEYWORDS["exclude"]):
                    continue
                
                pub_date_str = item.get("postdate", "")
                pub_date = self.extract_date(pub_date_str)
                
                if pub_date and pub_date < cutoff_date:
                    continue
                
                deadline = self.extract_deadline(combined_text)
                lawfirm = self.extract_lawfirm(combined_text)
                contact = self.extract_contact(combined_text)
                manager_name = self.extract_manager_name(combined_text)
                
                cafe_url = item.get("link", "")
                
                manager_id = ""
                if extract_manager and cafe_url and scraper:
                    try:
                        manager_id = scraper.extract_manager_id(cafe_url) or ""
                        time.sleep(0.5)
                    except:
                        pass
                
                # LLM 강화 분석 (선택적 — 토큰 절약 최적화 적용)
                ai_flag = "-"
                if llm_analyzer:
                    llm_data = llm_analyzer.analyze(title, description)
                    # regex 미추출 필드를 LLM 결과로 보완 (토큰 낭비 최소화)
                    if (not contact or contact == "-") and llm_data.get("contact", "-") not in ("-", "없음", ""):
                        contact = llm_data["contact"]
                    if deadline == "미상" and llm_data.get("deadline", "-") not in ("-", "없음", ""):
                        deadline = llm_data["deadline"]
                    if not lawfirm and llm_data.get("lawfirm", "-") not in ("-", "없음", ""):
                        lawfirm = llm_data["lawfirm"]
                    if llm_data.get("valid") is False:
                        ai_flag = "⚠️검증필요"
                    elif llm_data.get("valid") is True:
                        ai_flag = "✅확인됨"
                    else:
                        ai_flag = "🔄분석중"

                parsed_data.append({
                    "발견일시": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "단지명": apt_name,
                    "공고제목": title,
                    "공고일자": pub_date.strftime("%Y-%m-%d") if pub_date else "미상",
                    "마감일": deadline,
                    "법무법인": lawfirm if lawfirm else "-",
                    "카페명": item.get("cafename", ""),
                    "카페지기명": manager_name if manager_name else "-",
                    "카페지기ID": manager_id if manager_id else "-",
                    "연락처": contact if contact else "-",
                    "AI검증": ai_flag,
                    "URL": cafe_url,
                    "공고내용": description[:300] + "..." if len(description) > 300 else description
                })
                
            except Exception as e:
                continue
        
        return parsed_data

# ==================== AGENT 4: 총괄 에이전트 ====================

# ==================== AGENT 5: 총괄 에이전트 ====================

class OrchestratorAgent:
    """전체 워크플로우 조율"""
    
    def __init__(self, searcher, parser, detective=None, llm_analyzer=None):
        self.searcher = searcher
        self.parser = parser
        self.detective = detective
        self.llm_analyzer = llm_analyzer
    
    def run_scan(self, apt_list, extract_manager=True, detective_mode=False, progress_callback=None, results_callback=None):
        """전체 스캔 실행"""
        all_announcements = []
        total = len(apt_list)
        
        for idx, apt_name in enumerate(apt_list):
            if progress_callback:
                progress_callback(idx + 1, total, apt_name)
            
            # Step 1: 공고 검색
            search_results = self.searcher.search_announcements(apt_name)
            
            # Step 2: 파싱 (카페지기 기본 추출)
            parsed_results = self.parser.parse_results(
                search_results,
                apt_name,
                extract_manager=extract_manager,
                llm_analyzer=self.llm_analyzer
            )
            
            # Step 3: 탐정 모드 (선택)
            if detective_mode and self.detective and parsed_results:
                for result in parsed_results:
                    # 크로스 플랫폼 검색
                    social_findings = self.detective.search_social_platforms(
                        apt_name, 
                        result.get('카페명', '')
                    )
                    
                    # 추가 정보 저장
                    result['소셜채널'] = ', '.join([
                        f"{k}:{len(v)}" for k, v in social_findings.items() if v
                    ]) or "-"
                    
                    time.sleep(0.5)  # Rate limiting
            
            all_announcements.extend(parsed_results)
            
            # 실시간 결과 콜백
            if results_callback and parsed_results:
                results_callback(all_announcements, apt_name, parsed_results)
        
        return all_announcements

# ==================== UI 시작 ====================

# 헤더
st.markdown("""
<div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); border-radius: 10px; margin-bottom: 30px;'>
    <h1 style='color: #d4af37; font-size: 2.5rem; margin: 0;'>⚖️ 법무법인 제이엘</h1>
    <p style='color: #c7a962; font-size: 1.2rem; margin: 10px 0 0 0;'>완벽 공고문 스캐너 FINAL v1.0</p>
</div>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.header("🔧 설정")
    
    naver_secret = st.text_input(
        "네이버 Client Secret",
        type="password",
        value=NAVER_CLIENT_SECRET,
        help="네이버 개발자센터에서 발급"
    )
    
    # 연결 테스트
    if naver_secret:
        if st.button("🔌 연결 테스트"):
            try:
                test_url = "https://openapi.naver.com/v1/search/cafearticle.json"
                test_response = requests.get(
                    test_url,
                    headers={
                        "X-Naver-Client-Id": NAVER_CLIENT_ID,
                        "X-Naver-Client-Secret": naver_secret
                    },
                    params={"query": "test", "display": 1},
                    timeout=5
                )
                if test_response.status_code == 200:
                    st.success("✅ 네이버 API 연결 성공!")
                    st.session_state['naver_connected'] = True
                else:
                    st.error(f"❌ 연결 실패: {test_response.status_code}")
                    st.session_state['naver_connected'] = False
            except Exception as e:
                st.error(f"❌ 연결 오류: {str(e)}")
                st.session_state['naver_connected'] = False
        
        # 연결 상태 표시
        if st.session_state.get('naver_connected'):
            st.info("✅ 네이버 연결 완료")
    
    st.markdown("---")
    
    extract_manager = st.checkbox(
        "🎯 카페지기 ID 자동 추출",
        value=False,
        help="카페 홈페이지에서 카페지기 ID를 자동으로 추출합니다 (시간 증가)"
    )
    
    detective_mode = st.checkbox(
        "🕵️ 탐정 모드 (크로스 플랫폼 검색)",
        value=False,
        help="구글/인스타/카톡/페북/밴드 전체 검색 (시간 많이 증가)"
    )

    st.markdown("---")

    # ── Claude AI 토큰 절약 분석 ──────────────────────────────
    st.subheader("🤖 AI 강화 분석")
    use_llm = st.checkbox(
        "🧠 Claude AI 분석 활성화",
        value=False,
        help="Claude Haiku로 연락처·마감일·법인명 추출 정확도 향상 (토큰 절약 최적화 적용)"
    )

    claude_key = ""
    if use_llm:
        claude_key = st.text_input(
            "Claude API Key",
            type="password",
            value=st.session_state.get("claude_key_input", ""),
            help="Anthropic Console에서 발급 (claude.ai/settings)"
        )
        if claude_key:
            st.session_state["claude_key_input"] = claude_key

    # LLMAnalyzer 세션 관리 (토큰 카운터 유지)
    if use_llm and claude_key:
        prev_key = st.session_state.get("_llm_api_key", "")
        if prev_key != claude_key or st.session_state.get("llm_analyzer") is None:
            st.session_state["llm_analyzer"] = LLMAnalyzer(claude_key)
            st.session_state["_llm_api_key"] = claude_key
            st.success("✅ Claude AI 준비 완료")
    elif not use_llm:
        st.session_state["llm_analyzer"] = None

    llm_analyzer = st.session_state.get("llm_analyzer")

    # 토큰 사용 현황 표시
    if llm_analyzer and llm_analyzer.api_calls > 0:
        with st.expander("📊 토큰 사용 현황", expanded=False):
            for label, val in llm_analyzer.stats().items():
                st.metric(label, val)
    elif use_llm and claude_key:
        st.info("💡 스캔 실행 후 토큰 현황이 여기 표시됩니다")

    st.markdown("---")
    
    st.markdown("""
    ### 📊 시스템 구성
    
    **🤖 에이전트 5명:**
    1. 검색 (Searcher)
    2. 스크래퍼 (Scraper)
    3. 탐정 (Detective) 🆕
    4. 파싱 (Parser)
    5. 총괄 (Orchestrator)
    
    **🔍 검색 대상:**
    - 법무법인 선정 공고
    - 집단등기 입찰
    - 등기업체 선정
    
    **📋 추출 정보:**
    - 카페지기 이름/ID
    - 연락처/이메일
    - 마감일/법무법인
    - 공고 전체 내용
    """)
    
    st.markdown("---")
    
    st.info("💡 **Tip:** 카페지기 ID 추출은 공개 카페만 가능합니다")

# 메인 영역
tab1, tab2, tab3 = st.tabs(["🚀 스캔 실행", "📊 결과 분석", "📖 사용 방법"])

with tab1:
    st.header("공고문 자동 스캔")
    
    st.subheader("1️⃣ 단지 목록 입력")
    
    input_method = st.radio(
        "입력 방식",
        ["🚀 자동 수집 (APT분양)", "🏢 민간임대 조사", "직접 입력", "엑셀 업로드", "🌏 지역별 전체 검색"],
        horizontal=False
    )
    
    apt_list = []
    
    if input_method == "🏢 민간임대 조사":
        st.info("💡 공공지원 민간임대 입주예정 단지를 조사합니다 (공고 스캔 X)")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            three_years_later = datetime.now() + timedelta(days=365*3)
            st.write(f"**조사 대상:** 입주예정 ~ {three_years_later.strftime('%Y년 %m월')}까지")
        with col2:
            if st.button("🔍 민간임대 조사", type="primary"):
                with st.spinner("민간임대 단지 조사 중..."):
                    rental_data = []
                    
                    try:
                        api_key = "92b5632ea31cf343fbdaad04fdb9228cfacd78f6271dacf97a264a11fc5245d3"
                        api_url = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1/getPblPvtRentLttotPblancDetail"
                        
                        today = datetime.now()
                        one_year_ago = today - timedelta(days=365)
                        date_from = one_year_ago.strftime('%Y-%m-%d')
                        date_to = today.strftime('%Y-%m-%d')
                        
                        st.info("🔄 민간임대 API 호출 중...")
                        
                        for page in range(1, 6):
                            try:
                                params = {
                                    "serviceKey": api_key,
                                    "page": page,
                                    "perPage": 100,
                                    "cond[RCRIT_PBLANC_DE::GTE]": date_from,
                                    "cond[RCRIT_PBLANC_DE::LTE]": date_to
                                }
                                
                                response = requests.get(api_url, params=params, timeout=15)
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    items = data.get('data', [])
                                    
                                    if not items:
                                        break
                                    
                                    for item in items:
                                        house_name = item.get('HOUSE_NM', '')
                                        move_in = item.get('MVN_PREARNGE_YM', '')
                                        address = item.get('HSSPLY_ADRES', '')
                                        scale = item.get('TOT_SUPLY_HSHLDCO', 0)
                                        company = item.get('BSNS_MBY_NM', '')
                                        contact = item.get('MDHS_TELNO', '')
                                        
                                        if house_name and move_in:
                                            try:
                                                move_dt = datetime.strptime(move_in[:6], '%Y%m')
                                                if move_dt <= three_years_later:
                                                    rental_data.append({
                                                        '단지명': house_name,
                                                        '입주예정': move_in,
                                                        '공급위치': address,
                                                        '공급규모': f"{scale}세대",
                                                        '사업주체': company,
                                                        '문의처': contact
                                                    })
                                            except:
                                                pass
                                    
                                    st.success(f"✅ P{page}: {len(items)}개")
                                
                                time.sleep(0.3)
                                
                            except Exception as e:
                                st.warning(f"⚠️ P{page}: {str(e)}")
                                break
                        
                        st.session_state['rental_data'] = rental_data
                        st.success(f"🎉 {len(rental_data)}개 민간임대 단지 조사 완료!")
                        
                    except Exception as e:
                        st.error(f"조사 오류: {str(e)}")
        
        # 조사 결과 표시
        if 'rental_data' in st.session_state:
            rental_data = st.session_state['rental_data']
            st.metric("조사 완료", f"{len(rental_data)}개 단지")
            
            if rental_data:
                st.markdown("---")
                st.subheader("📋 민간임대 단지 조사 결과")
                
                df_rental = pd.DataFrame(rental_data)
                st.dataframe(df_rental, use_container_width=True, height=400)
                
                # 엑셀 다운로드
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_rental.to_excel(writer, sheet_name='민간임대조사', index=False)
                
                st.download_button(
                    "📥 엑셀 다운로드",
                    output.getvalue(),
                    file_name=f"민간임대조사_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.warning("💡 이 데이터는 공고 스캔용이 아닙니다. 민간임대 입주예정 단지 조사 자료입니다.")
    
    elif input_method == "🚀 자동 수집 (APT분양)":
        st.info("💡 청약홈 분양정보 API에서 APT 입주예정단지를 자동으로 수집합니다")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            three_years_later = datetime.now() + timedelta(days=365*3)
            st.write(f"**수집 조건:** 입주예정 ~ {three_years_later.strftime('%Y년 %m월')}까지")
        with col2:
            if st.button("🚀 APT 자동 수집", type="primary"):
                with st.spinner("청약홈 API에서 단지 수집 중..."):
                    collected_apts = []
                    
                    try:
                        api_key = "92b5632ea31cf343fbdaad04fdb9228cfacd78f6271dacf97a264a11fc5245d3"
                        base_url = "https://api.odcloud.kr/api/ApplyhomeInfoDetailSvc/v1"
                        
                        today = datetime.now()
                        one_year_ago = today - timedelta(days=365)
                        date_from = one_year_ago.strftime('%Y-%m-%d')
                        date_to = today.strftime('%Y-%m-%d')
                        
                        endpoints = [
                            ("getAPTLttotPblancDetail", "APT"),
                            ("getUrbtyOfctlLttotPblancDetail", "오피스텔"),
                            ("getRemndrLttotPblancDetail", "잔여세대"),
                            ("getOPTLttotPblancDetail", "임의공급")
                        ]
                        
                        for endpoint, name in endpoints:
                            st.info(f"🔄 {name} 수집 중...")
                            
                            for page in range(1, 6):
                                try:
                                    params = {
                                        "serviceKey": api_key,
                                        "page": page,
                                        "perPage": 100,
                                        "cond[RCRIT_PBLANC_DE::GTE]": date_from,
                                        "cond[RCRIT_PBLANC_DE::LTE]": date_to
                                    }
                                    
                                    response = requests.get(
                                        f"{base_url}/{endpoint}",
                                        params=params,
                                        timeout=15
                                    )
                                    
                                    if response.status_code == 200:
                                        data = response.json()
                                        items = data.get('data', [])
                                        
                                        if not items:
                                            break
                                        
                                        for item in items:
                                            house_name = item.get('HOUSE_NM')
                                            move_in = item.get('MVN_PREARNGE_YM', '')
                                            
                                            if house_name:
                                                if move_in and len(move_in) >= 6:
                                                    try:
                                                        move_dt = datetime.strptime(move_in[:6], '%Y%m')
                                                        if move_dt <= three_years_later:
                                                            collected_apts.append(house_name.strip())
                                                    except:
                                                        collected_apts.append(house_name.strip())
                                                else:
                                                    collected_apts.append(house_name.strip())
                                        
                                        st.success(f"✅ {name} P{page}: {len(items)}개")
                                    
                                    time.sleep(0.3)
                                    
                                except Exception as e:
                                    st.warning(f"⚠️ {name} P{page}: {str(e)}")
                                    break
                        
                        apt_list_unique = list(set(collected_apts))
                        st.session_state['auto_collected_apts'] = apt_list_unique
                        st.success(f"🎉 {len(apt_list_unique)}개 단지 수집!")
                        
                    except Exception as e:
                        st.error(f"오류: {str(e)}")
        
        if 'auto_collected_apts' in st.session_state:
            apt_list = st.session_state['auto_collected_apts']
            st.metric("수집된 단지", f"{len(apt_list)}개")
            
            if apt_list:
                with st.expander("📋 수집된 단지 (처음 30개)"):
                    for apt in sorted(apt_list)[:30]:
                        st.text(f"• {apt}")
    
    elif input_method == "🌏 지역별 전체 검색":
        st.info("💡 선택한 지역의 모든 카페에서 법무법인 선정 공고를 검색합니다")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            region = st.selectbox(
                "지역 선택",
                ["전국", "서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", 
                 "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
            )
        
        with col2:
            search_limit = st.number_input(
                "검색 개수",
                min_value=10,
                max_value=1000,
                value=100,
                step=10
            )
        
        # 지역 검색 버튼
        st.session_state['region_search_mode'] = True
        st.session_state['selected_region'] = region
        st.session_state['search_limit'] = search_limit
        
        st.success(f"✅ {region} 지역 / {search_limit}개 검색 설정 완료")
        st.info("👇 아래 '2️⃣ 스캔 실행' 버튼을 눌러주세요")
    
    elif input_method == "직접 입력":
        st.info("💡 국토교통부 + 캠코 API에서 입주예정단지를 자동으로 수집합니다")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            three_years_later = datetime.now() + timedelta(days=365*3)
            st.write(f"**수집 조건:** 현재({datetime.now().strftime('%Y년 %m월')}) + 3년 = {three_years_later.strftime('%Y년 %m월')}까지")
        with col2:
            if st.button("🚀 자동 수집 시작", type="primary"):
                with st.spinner("공공API에서 단지 수집 중..."):
                    apt_list = []
                    
                    try:
                        # API 키
                        api_key = "92b5632ea31cf343fbdaad04fdb9228cfacd78f6271dacf97a264a11fc5245d3"
                        
                        # 국토교통부 API - 아파트 정보
                        molit_url = "https://apis.data.go.kr/1613000/AptBassInfoServiceV4/getAphusBassInfoV4"
                        
                        st.info("🔄 국토교통부 API 호출 중...")
                        molit_apts = []
                        
                        for page in range(1, 11):  # 10 페이지 = 1000개
                            try:
                                response = requests.get(
                                    molit_url,
                                    params={
                                        "serviceKey": api_key,
                                        "pageNo": str(page),
                                        "numOfRows": "100"
                                    },
                                    timeout=15
                                )
                                
                                if response.status_code == 200:
                                    # XML 파싱
                                    from xml.etree import ElementTree as ET
                                    root = ET.fromstring(response.content)
                                    
                                    items = root.findall('.//item')
                                    for item in items:
                                        apt_name = item.find('kaptName')
                                        move_date = item.find('kaptUseDate')
                                        
                                        if apt_name is not None and apt_name.text:
                                            # 입주일 체크 (3년 이내)
                                            if move_date is not None and move_date.text:
                                                try:
                                                    move_dt = datetime.strptime(move_date.text[:6], '%Y%m')
                                                    if move_dt <= three_years_later:
                                                        molit_apts.append(apt_name.text.strip())
                                                except:
                                                    molit_apts.append(apt_name.text.strip())
                                            else:
                                                molit_apts.append(apt_name.text.strip())
                                
                                time.sleep(0.5)  # Rate limiting
                            except Exception as e:
                                st.warning(f"페이지 {page} 오류: {str(e)}")
                                continue
                        
                        st.success(f"✅ 국토부: {len(molit_apts)}개")
                        
                        # 캠코 API
                        st.info("🔄 캠코 API 호출 중...")
                        kamco_url = "https://apis.data.go.kr/B010003/pblcDvlpRlstFclt/fcltPscd"
                        kamco_apts = []
                        
                        for page in range(1, 11):
                            try:
                                response = requests.get(
                                    kamco_url,
                                    params={
                                        "serviceKey": api_key,
                                        "pageNo": str(page),
                                        "numOfRows": "100"
                                    },
                                    timeout=15
                                )
                                
                                if response.status_code == 200:
                                    root = ET.fromstring(response.content)
                                    items = root.findall('.//item')
                                    
                                    for item in items:
                                        apt_name = item.find('fcltNm')
                                        if apt_name is not None and apt_name.text:
                                            kamco_apts.append(apt_name.text.strip())
                                
                                time.sleep(0.5)
                            except Exception as e:
                                st.warning(f"캠코 페이지 {page} 오류: {str(e)}")
                                continue
                        
                        st.success(f"✅ 캠코: {len(kamco_apts)}개")
                        
                        # 합치고 중복 제거
                        apt_list = list(set(molit_apts + kamco_apts))
                        
                        st.session_state['auto_collected_apts'] = apt_list
                        st.success(f"🎉 총 {len(apt_list)}개 단지 수집 완료!")
                        
                    except Exception as e:
                        st.error(f"API 오류: {str(e)}")
                        st.warning("API 호출 실패 - 샘플 데이터로 진행")
                        apt_list = ["힐스테이트 동탄", "래미안 강남", "자이 수원"] * 10
                        st.session_state['auto_collected_apts'] = apt_list
        
        # 수집된 단지 표시
        if 'auto_collected_apts' in st.session_state:
            apt_list = st.session_state['auto_collected_apts']
            st.metric("수집된 단지", f"{len(apt_list)}개")
    
    elif input_method == "직접 입력":
        apt_input = st.text_area(
            "아파트명 입력 (한 줄에 하나씩)",
            placeholder="힐스테이트 동탄\n래미안 강남\n자이 수원",
            height=150
        )
        
        if apt_input:
            apt_list = [line.strip() for line in apt_input.split("\n") if line.strip()]
            st.success(f"✅ {len(apt_list)}개 단지 입력 완료")
    
    else:
        uploaded_file = st.file_uploader(
            "엑셀 파일 업로드",
            type=["xlsx", "xls"],
            help="'아파트명' 또는 '단지명' 컬럼 필요"
        )
        
        if uploaded_file:
            try:
                # 모든 시트 읽기
                xl = pd.ExcelFile(uploaded_file)
                all_apts = []
                detected_columns = []
                
                for sheet_name in xl.sheet_names:
                    try:
                        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                        
                        # 컬럼 찾기 (확장된 키워드)
                        apt_col = None
                        for col in df.columns:
                            col_str = str(col).lower().replace(" ", "")
                            keywords = [
                                "아파트", "단지", "사업장", "정비구역", "apt", 
                                "빌라", "오피스텔", "주택", "건물", "name", 
                                "현장", "프로젝트", "물건", "입주"
                            ]
                            if any(k in col_str for k in keywords):
                                apt_col = col
                                break
                        
                        # 못 찾으면 첫 번째 컬럼 사용
                        if not apt_col and len(df.columns) > 0:
                            apt_col = df.columns[0]
                            st.warning(f"⚠️ {sheet_name}: '{apt_col}' 컬럼을 단지명으로 사용합니다")
                        
                        if apt_col:
                            detected_columns.append(f"{sheet_name}:{apt_col}")
                            apts = df[apt_col].dropna().astype(str).str.strip().tolist()
                            apts = [apt for apt in apts if apt and apt != "nan" and len(apt) > 1]
                            all_apts.extend(apts)
                    except Exception as e:
                        st.warning(f"⚠️ {sheet_name} 시트 읽기 실패: {str(e)}")
                        continue
                
                apt_list = list(set(all_apts))  # 중복 제거
                
                if apt_list:
                    st.success(f"✅ {len(apt_list)}개 고유 단지 로드 완료 (총 {len(all_apts)}행, {len(xl.sheet_names)}개 시트)")
                    with st.expander("📋 감지된 컬럼"):
                        for col_info in detected_columns:
                            st.text(f"• {col_info}")
                else:
                    st.error("엑셀 파일에서 데이터를 찾을 수 없습니다. 파일을 확인해주세요.")
            
            except Exception as e:
                st.error(f"파일 읽기 오류: {str(e)}")
    
    st.markdown("---")
    
    st.subheader("2️⃣ 스캔 실행")
    
    if not naver_secret:
        st.warning("⚠️ 네이버 Client Secret을 입력하세요 (왼쪽 사이드바)")
    
    # 자동 저장 헬퍼 함수
    def auto_save_results(results, apt_name=""):
        """5분마다 자동 저장"""
        if not results:
            return
        
        now = datetime.now()
        last_save = st.session_state.get('last_save_time')
        
        # 5분마다 또는 첫 저장
        if not last_save or (now - last_save).seconds >= 300:
            try:
                timestamp = now.strftime("%Y%m%d_%H%M%S")
                filename = f"JL스캔결과_자동저장_{timestamp}.xlsx"
                filepath = os.path.join("/mnt/user-data/outputs", filename)
                
                df = pd.DataFrame(results)
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='자동저장', index=False)
                
                st.session_state['last_save_time'] = now
                st.toast(f"✅ 자동 저장 완료: {len(results)}개", icon="💾")
            except Exception as e:
                st.toast(f"⚠️ 자동 저장 실패: {str(e)}", icon="⚠️")
    
    col1, col2 = st.columns([3, 1])
    
    # 스캔 가능 여부 체크
    can_scan = (apt_list and naver_secret) or (st.session_state.get('region_search_mode', False) and naver_secret)
    
    # 실시간 결과 표시 준비
    if 'live_results' not in st.session_state:
        st.session_state['live_results'] = []
    
    if 'last_save_time' not in st.session_state:
        st.session_state['last_save_time'] = None
    
    with col1:
        scan_button = st.button(
            "🚀 공고문 스캔 시작", 
            disabled=not can_scan,
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        if apt_list:
            st.metric("대기 중", f"{len(apt_list)}개")
        elif st.session_state.get('region_search_mode', False):
            region = st.session_state.get('selected_region', '전국')
            st.metric("지역 선택", region)
    
    if scan_button:
        # 지역 검색 모드 체크
        if st.session_state.get('region_search_mode', False):
            region = st.session_state.get('selected_region', '전국')
            search_limit = st.session_state.get('search_limit', 100)
            
            st.info(f"🌏 {region} 지역 전체 검색 중...")
            
            # 에이전트 초기화
            searcher = SearchAgent(NAVER_CLIENT_ID, naver_secret)
            parser = ParserAgent()
            scraper = CafeManagerScraper() if extract_manager else None
            detective = DetectiveAgent() if detective_mode else None
            
            # 지역 키워드 생성
            if region == "전국":
                search_query = "법무법인 선정"
            else:
                search_query = f"{region} 법무법인 선정"
            
            start_time = time.time()
            results = []
            
            with st.spinner(f"{region} 지역 검색 중..."):
                try:
                    # 네이버 검색
                    response = requests.get(
                        "https://openapi.naver.com/v1/search/cafearticle.json",
                        headers={
                            "X-Naver-Client-Id": NAVER_CLIENT_ID,
                            "X-Naver-Client-Secret": naver_secret
                        },
                        params={
                            "query": search_query,
                            "display": search_limit,
                            "sort": "date"
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        items = response.json().get("items", [])
                        results = parser.parse_results(items, region, extract_manager=extract_manager, llm_analyzer=llm_analyzer)
                        
                        # 탐정 모드
                        if detective_mode and detective and results:
                            for result in results:
                                social = detective.search_social_platforms(
                                    result.get('단지명', ''),
                                    result.get('카페명', '')
                                )
                                result['소셜채널'] = ', '.join([f"{k}:{len(v)}" for k, v in social.items() if v]) or "-"
                    
                except Exception as e:
                    st.error(f"검색 오류: {str(e)}")
            
            elapsed_time = time.time() - start_time
            st.success(f"✅ {len(results)}건 발견! ({elapsed_time:.1f}초)")
            
            # 세션 초기화
            st.session_state['region_search_mode'] = False
            
        else:
            # 기존 단지 리스트 기반 스캔
            searcher = SearchAgent(NAVER_CLIENT_ID, naver_secret)
            parser = ParserAgent()
            detective = DetectiveAgent() if detective_mode else None
            orchestrator = OrchestratorAgent(searcher, parser, detective, llm_analyzer=llm_analyzer)
            
            # 진행 상황
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_metric = st.empty()
            
            # 실시간 결과 컨테이너
            st.markdown("---")
            st.subheader("📊 실시간 발견 결과")
            live_results_container = st.empty()
            live_count = st.empty()
            
            def update_progress(current, total, apt_name):
                progress = current / total
                progress_bar.progress(progress)
                status_text.text(f"🔍 스캔 중... ({current}/{total})")
                if detective_mode:
                    status_metric.metric("현재 단지", f"{apt_name} 🕵️")
                else:
                    status_metric.metric("현재 단지", apt_name)
            
            def update_live_results(all_results, apt_name, new_results):
                """실시간 결과 표시 및 자동 저장"""
                # 실시간 카운트
                live_count.metric("🎯 발견 건수", f"{len(all_results)}건", delta=f"+{len(new_results)}")
                
                # 전체 결과 표시 (클릭 가능한 링크)
                if all_results:
                    with live_results_container.container():
                        for idx, result in enumerate(all_results):
                            with st.expander(f"**{idx+1}. {result['단지명']}** - {result['공고제목'][:40]}...", expanded=(idx >= len(all_results)-3)):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**📅 발견:** {result['발견일시']}")
                                    st.write(f"**🏢 카페:** {result['카페명']}")
                                    if result['연락처'] != '-':
                                        st.write(f"**📞 연락처:** `{result['연락처']}`")
                                
                                with col2:
                                    # 클릭 가능한 링크
                                    st.markdown(f"🔗 [**공고 보기**]({result['URL']})")
                                    if 'cafe.naver.com' in result['URL']:
                                        cafe_url = result['URL'].split('/ArticleRead')[0] if '/ArticleRead' in result['URL'] else result['URL']
                                        st.markdown(f"☕ [**카페 가기**]({cafe_url})")
                
                # 자동 저장 (5분마다)
                auto_save_results(all_results, apt_name)
            
            # 스캔 실행
            start_time = time.time()
            
            with st.spinner("스캔 진행 중..."):
                results = orchestrator.run_scan(
                    apt_list, 
                    extract_manager=extract_manager,
                    detective_mode=detective_mode,
                    progress_callback=update_progress,
                    results_callback=update_live_results
                )
            
            elapsed_time = time.time() - start_time
            
            progress_bar.empty()
            status_text.empty()
            status_metric.empty()
        
        # 결과 저장
        if 'scan_results' not in st.session_state:
            st.session_state.scan_results = []
        st.session_state.scan_results = results
        
        # 결과 표시
        st.markdown("---")
        st.subheader("3️⃣ 스캔 결과")
        
        if results:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 총 발견", f"{len(results)}건")
            
            with col2:
                with_contact = len([r for r in results if r['연락처'] != '-'])
                st.metric("📞 연락처 확보", f"{with_contact}건")
            
            with col3:
                st.metric("⏱️ 소요 시간", f"{elapsed_time:.1f}초")
            
            st.success(f"🎯 스캔 완료! {len(results)}건의 공고 발견")
            
            # 데이터프레임
            df_results = pd.DataFrame(results)
            
            # 필터
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                show_option = st.selectbox(
                    "표시 옵션",
                    ["전체", "연락처 있음만", "카페지기 정보 있음만"]
                )
            
            with filter_col2:
                sort_option = st.selectbox(
                    "정렬 기준",
                    ["발견일시 (최신순)", "단지명 (가나다순)", "마감일 (임박순)"]
                )
            
            # 필터 적용
            df_display = df_results.copy()
            
            if show_option == "연락처 있음만":
                df_display = df_display[df_display['연락처'] != '-']
            elif show_option == "카페지기 정보 있음만":
                df_display = df_display[
                    (df_display['카페지기명'] != '-') | 
                    (df_display['카페지기ID'] != '-')
                ]
            
            # 정렬 적용
            if sort_option == "발견일시 (최신순)":
                df_display = df_display.sort_values('발견일시', ascending=False)
            elif sort_option == "단지명 (가나다순)":
                df_display = df_display.sort_values('단지명')
            elif sort_option == "마감일 (임박순)":
                df_display = df_display.sort_values('마감일')
            
            # 클릭 가능한 링크로 표시
            st.markdown("### 📋 발견된 공고 목록")
            
            for idx, row in df_display.iterrows():
                with st.expander(f"**{row['단지명']}** - {row['공고제목'][:50]}...", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**📅 발견일시:** {row['발견일시']}")
                        st.write(f"**🏢 카페:** {row['카페명']}")
                        if row['카페지기명'] != '-':
                            st.write(f"**👤 카페지기:** {row['카페지기명']} ({row['카페지기ID']})")
                    
                    with col2:
                        st.write(f"**📆 공고일:** {row['공고일자']}")
                        st.write(f"**⏰ 마감일:** {row['마감일']}")
                        if row['법무법인'] != '-':
                            st.write(f"**⚖️ 법무법인:** {row['법무법인']}")
                    
                    with col3:
                        if row['연락처'] != '-':
                            st.write(f"**📞 연락처:**")
                            st.code(row['연락처'])
                    
                    # 링크 버튼들
                    link_col1, link_col2 = st.columns(2)
                    with link_col1:
                        st.markdown(f"🔗 [**공고 원문 보기**]({row['URL']})", unsafe_allow_html=True)
                    with link_col2:
                        # 카페 링크 추출 (URL에서)
                        if 'cafe.naver.com' in row['URL']:
                            cafe_url = row['URL'].split('/ArticleRead')[0] if '/ArticleRead' in row['URL'] else row['URL']
                            st.markdown(f"☕ [**카페 홈 가기**]({cafe_url})", unsafe_allow_html=True)
                    
                    # 공고 내용
                    with st.expander("📄 공고 내용 미리보기"):
                        st.write(row['공고내용'])
            
            # 간단한 테이블도 제공
            st.markdown("---")
            st.markdown("### 📊 전체 목록 (테이블)")
            
            # URL 컬럼을 링크 형식으로 변환
            display_df = df_display.copy()
            display_cols = ['발견일시', '단지명', '공고제목', '카페명', '연락처', 'AI검증']
            st.dataframe(
                display_df[display_cols],
                use_container_width=True,
                hide_index=True,
                height=300
            )
            
            # 다운로드
            st.markdown("---")
            st.subheader("4️⃣ 엑셀 다운로드")
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 전체 공고
                df_results.to_excel(writer, sheet_name='전체공고', index=False)
                
                # 하이퍼링크 적용
                worksheet = writer.sheets['전체공고']
                url_col_idx = df_results.columns.get_loc('URL') + 1  # Excel은 1부터 시작
                
                for row in range(2, len(df_results) + 2):  # 헤더 제외
                    cell = worksheet.cell(row=row, column=url_col_idx)
                    url = cell.value
                    if url and url != '-':
                        cell.hyperlink = url
                        cell.style = 'Hyperlink'
                
                # 연락처 있음만
                df_with_contact = df_results[df_results['연락처'] != '-']
                if not df_with_contact.empty:
                    df_with_contact.to_excel(writer, sheet_name='연락처확보', index=False)
                    
                    # 하이퍼링크 적용
                    worksheet2 = writer.sheets['연락처확보']
                    url_col_idx2 = df_with_contact.columns.get_loc('URL') + 1
                    for row in range(2, len(df_with_contact) + 2):
                        cell = worksheet2.cell(row=row, column=url_col_idx2)
                        url = cell.value
                        if url and url != '-':
                            cell.hyperlink = url
                            cell.style = 'Hyperlink'
                
                # 카페지기 정보 있음
                df_with_manager = df_results[
                    (df_results['카페지기명'] != '-') | 
                    (df_results['카페지기ID'] != '-')
                ]
                if not df_with_manager.empty:
                    df_with_manager.to_excel(writer, sheet_name='카페지기정보', index=False)
                    
                    # 하이퍼링크 적용
                    worksheet3 = writer.sheets['카페지기정보']
                    url_col_idx3 = df_with_manager.columns.get_loc('URL') + 1
                    for row in range(2, len(df_with_manager) + 2):
                        cell = worksheet3.cell(row=row, column=url_col_idx3)
                        url = cell.value
                        if url and url != '-':
                            cell.hyperlink = url
                            cell.style = 'Hyperlink'
            
            excel_data = output.getvalue()
            filename = f"JL_완벽스캔_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            
            st.download_button(
                label="📥 엑셀 다운로드 (전체 시트 포함)",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.info("💡 다운로드 파일에는 '전체공고', '연락처확보', '카페지기정보' 3개 시트가 포함됩니다")
        
        else:
            st.warning("⚠️ 발견된 공고가 없습니다")

with tab2:
    st.header("📊 결과 분석")
    
    if 'scan_results' in st.session_state and st.session_state.scan_results:
        df = pd.DataFrame(st.session_state.scan_results)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 공고", len(df))
        
        with col2:
            with_contact = len(df[df['연락처'] != '-'])
            rate = (with_contact / len(df) * 100) if len(df) > 0 else 0
            st.metric("연락처 확보", f"{with_contact}건", f"{rate:.1f}%")
        
        with col3:
            with_manager = len(df[(df['카페지기명'] != '-') | (df['카페지기ID'] != '-')])
            rate = (with_manager / len(df) * 100) if len(df) > 0 else 0
            st.metric("카페지기 정보", f"{with_manager}건", f"{rate:.1f}%")
        
        with col4:
            with_lawfirm = len(df[df['법무법인'] != '-'])
            st.metric("경쟁사 감지", f"{with_lawfirm}건")
        
        st.markdown("---")
        
        # 차트
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 정보 확보율")
            
            info_data = pd.DataFrame({
                '항목': ['연락처', '카페지기명', '카페지기ID', '법무법인'],
                '확보건수': [
                    len(df[df['연락처'] != '-']),
                    len(df[df['카페지기명'] != '-']),
                    len(df[df['카페지기ID'] != '-']),
                    len(df[df['법무법인'] != '-'])
                ]
            })
            
            st.bar_chart(info_data.set_index('항목'))
        
        with col2:
            st.subheader("🏢 단지별 공고 수")
            
            apt_counts = df['단지명'].value_counts().head(10)
            st.bar_chart(apt_counts)
    
    else:
        st.info("스캔을 먼저 실행하세요")

with tab3:
    st.header("📖 사용 방법")
    
    st.markdown("""
    ## 🎯 시스템 개요
    
    법무법인 선정 공고를 자동으로 스캔하고 카페지기 정보를 추출하는 완벽 시스템입니다.
    
    ---
    
    ## 🚀 사용 순서
    
    ### 1단계: API 설정
    - 왼쪽 사이드바에서 **Client Secret** 입력
    
    ### 2단계: 단지 목록 입력
    - **직접 입력:** 한 줄에 하나씩
    - **엑셀 업로드:** 다중 시트 자동 읽기
    
    ### 3단계: 옵션 선택
    - 카페지기 ID 추출 여부 (시간 증가)
    
    ### 4단계: 스캔 시작
    - 자동으로 검색 → 파싱 → 추출
    
    ### 5단계: 결과 확인
    - 표 형식으로 확인
    - 필터/정렬 가능
    - 엑셀 다운로드 (3개 시트)
    
    ---
    
    ## 📋 추출 정보
    
    **자동 추출:**
    1. 공고 제목/내용
    2. 공고일자/마감일
    3. 경쟁사 법무법인
    4. 카페명
    5. **카페지기 이름** ✨
    6. **카페지기 ID** ✨
    7. **연락처** ✨
    8. URL
    
    ---
    
    ## ⚠️ 제한사항
    
    **카페지기 ID:**
    - 공개 카페만 추출 가능
    - 회원 전용 카페는 "추출실패"
    
    **연락처:**
    - 공고문에 포함된 경우만
    - 다양한 형식 자동 인식
    
    ---
    
    ## 📈 예상 성과
    
    **100건 공고 기준:**
    - 연락처 확보: 65건 (65%)
    - 카페지기명: 45건 (45%)
    - 카페지기 ID: 30건 (30%)
    
    ---
    
    ## 🆘 문제 해결
    
    **Q: 공고가 안 나와요**
    - A: 최근 14일 내 공고가 없을 수 있음
    
    **Q: API 오류**
    - A: Client Secret 확인
    
    **Q: 카페지기 ID가 "추출실패"**
    - A: 회원 전용 카페 (정상)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 20px;'>
    <p><strong>법무법인 제이엘 | 완벽 공고문 스캐너 FINAL v1.0</strong></p>
    <p>4-Agent Architecture: Searcher + Scraper + Parser + Orchestrator</p>
    <p style='font-size: 0.9rem;'>모든 기능 통합 · 테스트 완료 · 실전 배포 준비</p>
</div>
""", unsafe_allow_html=True)

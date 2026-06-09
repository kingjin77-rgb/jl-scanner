# KB증권 해외주식 자동매매 시스템

KB증권 OpenAPI를 활용한 해외주식(미국) 자동매매 프로그램입니다.

## 주요 기능

- **4가지 매매 전략**: 모멘텀, RSI, MACD, 볼린저밴드 복합 신호
- **리스크 관리**: 손절/수익실현/트레일링 스탑, Kelly Criterion 포지션 사이징, MDD 차단
- **실시간 WebSocket**: 실시간 시세 수신
- **텔레그램 알림**: 주문/체결/손익 실시간 알림
- **백테스트 엔진**: 샤프/소르티노/MDD/승률 분석
- **Streamlit 대시보드**: 포트폴리오 실시간 모니터링

## 빠른 시작

### 1. 패키지 설치
```bash
cd kb-auto-trader
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
cp .env.example .env
# .env 파일에 KB증권 API 키 입력
```

### 3. 모의투자 실행
```bash
python main.py --paper
```

### 4. 대시보드 실행
```bash
streamlit run dashboard/app.py
```

### 5. 백테스트 실행
```bash
python backtest_runner.py --strategy Combined --start 2023-01-01 --end 2024-12-31
```

## KB증권 API 키 발급

1. [KB증권 핀테크스토어](https://store.kbsec.com) 접속
2. 개발자 등록 및 앱 생성
3. `AppKey`, `AppSecret` 발급
4. `.env` 파일에 입력

## 설정 파일

`config/config.yaml`에서 다음을 조정하세요:

| 항목 | 기본값 | 설명 |
|------|--------|------|
| `stop_loss_pct` | 3.0% | 손절선 |
| `take_profit_pct` | 8.0% | 수익실현선 |
| `max_positions` | 10 | 최대 보유 종목 수 |
| `position_sizer` | kelly | 포지션 사이징 방식 |
| `max_drawdown_pct` | 15.0% | MDD 도달 시 거래 중단 |

## 디렉토리 구조

```
kb-auto-trader/
├── main.py                  # 자동매매 실행
├── backtest_runner.py       # 백테스트 실행
├── config/config.yaml       # 전체 설정
├── .env                     # API 키 (비공개)
├── kb_trader/
│   ├── api/                 # KB증권 API 클라이언트
│   ├── strategies/          # 매매 전략 (모멘텀/RSI/MACD/볼린저)
│   ├── risk/                # 리스크 관리
│   ├── order/               # 주문 관리
│   ├── portfolio/           # 포트폴리오 추적
│   ├── backtest/            # 백테스트 엔진
│   └── notification/        # 텔레그램 알림
└── dashboard/app.py         # Streamlit 대시보드
```

## 주의사항

- **실거래 전 반드시 모의투자로 충분히 테스트하세요**
- 자동매매는 손실이 발생할 수 있습니다
- `is_paper_trading: false` 설정 시 실제 거래가 실행됩니다
- API 키를 절대 공개 저장소에 업로드하지 마세요

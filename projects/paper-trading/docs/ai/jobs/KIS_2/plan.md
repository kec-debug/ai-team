# KIS_2 — 해외주식 계좌 / 주문 공식 문서값 catalog 채우기

## 1. 요청 요약

`docs/kis/MISSING_OFFICIAL_VALUES.md` 는 KIS Open API HTTP 연결에 필요한 공식 문서값 갭을 정리하는 문서다. KIS_1 에서 §1 OAuth 와 §3 해외주식 시세는 `MISSING_MARKET_DATA_VALUES.md` 라는 sub-catalog 로 보강 완료됐다. 본 KIS_2 는 같은 문서의 §2 (해외주식 계좌) 와 §4 (모의투자 주문) 두 섹션을 KIS Developers 공식 자료 `uploads/6.xlsx` 에 직접 명시된 값으로 채우는 **문서 전용 작업**이다.

핵심 제약:

- 자료 출처는 `uploads/6.xlsx` 한 파일로 한정. 다른 xlsx (`uploads/2.xlsx` 해외 streaming, `uploads/4.xlsx` 국내 시세, `uploads/5.xlsx` 국내 주문/계좌) 는 본 catalog 의 §2/§4 (해외주식) 범위가 아니므로 사용하지 않는다.
- `Confirmed: yes` 는 6.xlsx 의 해당 sheet 에 명시된 값에 한해 부여한다. 그 외는 `<TBD>` 와 `Confirmed: no` 로 유지한다.
- 모의투자 (paper) 지원 여부를 endpoint 단위로 명확히 구분한다. paper-미지원 endpoint 는 실전 TR ID 만 catalog 에 남기고 모의 TR ID 칸은 `모의투자 미지원` 으로 표기한다.
- KIS 모의투자가 LIMIT (`ORD_DVSN=00`) 외 주문 유형을 받지 않는다는 공식 명시 ("모의투자 VTTT1002U / VTTT1006U / VTTT1001U / VTTS1001U 등으로는 `00:지정가`만 가능") 를 그대로 옮긴다. 이는 본 저장소의 `OrderType.MARKET` 3중 가드와 일치하며 catalog 가 그 정책의 공식 근거를 제공한다.
- 실 app key / app secret / 계좌번호 / access token / Bearer / refresh token 값은 catalog 어디에도 기록하지 않는다.
- 코드 변경 0건. 테스트 변경 0건. CI 실행 없음.

## 2. 작업 범위

포함하는 것:

- `docs/kis/MISSING_OFFICIAL_VALUES.md` §2 (해외주식/미국주식 계좌) 의 단일 갭 표를 6.xlsx 기반 sub-table 세트로 교체.
- 같은 문서 §4 (모의투자 주문) 의 단일 갭 표를 6.xlsx 기반 sub-table 세트로 교체.
- 두 섹션 모두 다음 sub-table 구성:
  1. endpoint catalog (메뉴 / path / HTTP method / 실전 TR_ID / 모의 TR_ID / Confirmed).
  2. 공통 Request Header (KIS_1 의 시세 catalog 와 동일 형태).
  3. endpoint 별 핵심 Request query/body 필드.
  4. endpoint 별 핵심 Response body 필드.
  5. 모의투자 제약 (지원 ORD_DVSN, 모의 미지원 endpoint 목록, 모의 한정 EXCD 등).
- §1 OAuth / §3 시세 본문은 KIS_1 산출물 (`MISSING_MARKET_DATA_VALUES.md`) 이 보강 완료한 상태이므로 본 job 에서는 두 섹션의 표 본문을 **수정하지 않는다**. 단, "다음 작업 가이드" 와 "보안" 섹션 같은 일반 문구도 손대지 않는다.
- `patch.md` 에 채운 값 / 부족한 값 / `api-account-001` / `api-orders-paper-001` 진행 가능 여부 판단 정리.

제외 (절대 안 하는 것):

- `app/` 또는 `tests/` 또는 `app/broker/kis*.py` 의 어떤 코드 / 테스트 변경.
- KIS HTTP 호출 추가, endpoint 호출 실험.
- 외부 HTTP 라이브러리 추가.
- `app/api/`, `app/static/`, `app/main.py`, `app/config.py`, `app/oms/`, `app/risk/`, `app/portfolio/`, `app/strategy/`, `app/session/`, `app/runtime/` 등 어떤 GUI / 코어 모듈 수정.
- `.env`, `.env.example`, `.gitignore` 수정.
- live trading 활성화 / `OrderType.MARKET` 가드 우회 / `ALLOW_MARKET_ORDERS=true` 도입.
- 실 app key / app secret / 계좌번호 / access token / Bearer / refresh token 기록.
- KIS endpoint URL / TR ID / 헤더 / 응답 필드명 추측. 6.xlsx 에서 확인되지 않은 값은 `<TBD>` 로 남긴다.
- 다른 xlsx (2.xlsx 해외 streaming, 4.xlsx 국내 시세, 5.xlsx 국내 주문/계좌) 의 값을 본 catalog 에 옮기는 행위 — 본 catalog 는 해외주식 계좌/주문 범위.
- `MISSING_MARKET_DATA_VALUES.md` 수정.
- `docs/ai/MASTER_TRADING_ROADMAP.md`, `docs/ai/ROADMAP_STATUS.md` 등 다른 roadmap 문서 수정.
- 자동 git commit / push / merge / production deploy.

## 3. 수정해야 할 파일

수정 (MODIFY):

- `docs/kis/MISSING_OFFICIAL_VALUES.md` — §2 와 §4 본문을 codex-task §A 의 byte-level 본문으로 교체. §1 / §3 / 정책 머리말 / 다음 작업 가이드 / 보안 섹션은 손대지 않는다.

생성 (NEW):

- `projects/paper-trading/docs/ai/jobs/KIS_2/patch.md` — Codex 가 작성. 채워진 값 요약, 모의 미지원 endpoint 목록, 부족한 값, `api-account-001`/`api-orders-paper-001` 다음 단계 진행 가능 여부 판단.

손대지 않는 파일 (대표):

- `docs/kis/MISSING_MARKET_DATA_VALUES.md`.
- `app/`, `tests/` 의 모든 파일.
- `.env*`, `pyproject.toml`, `pytest.ini`, `README.md`.
- `uploads/*.xlsx` (읽기만, 수정 금지).

## 4. Codex 구현 지시문

자세한 단계와 byte-level 본문은 `codex-task.md` 에 기록한다. 요지:

1. **xlsx 재파싱 금지**. Codex 는 `uploads/6.xlsx` 를 다시 열지 않는다. 본 plan 의 §A 본문이 6.xlsx 의 19 개 sheet (API 목록 + 18 개 endpoint sheet) 에서 직접 확인된 값만 담고 있다. Codex 는 그 본문을 그대로 `docs/kis/MISSING_OFFICIAL_VALUES.md` 의 §2 와 §4 위치에 byte-level 로 적용한다.
2. **앵커 보존**: 기존 문서의 다음 헤딩과 본문은 손대지 않는다.
   - `# KIS Open API - Missing Official Values` 문서 제목.
   - `## 정책` 섹션 전체.
   - `## 1. OAuth 인증` 섹션 전체 (표 본문 포함).
   - `## 3. 해외주식/미국주식 시세` 섹션 전체 (표 본문 포함).
   - `## 다음 작업 가이드` 섹션 전체.
   - `## 보안` 섹션 전체.
3. **§2 와 §4 본문 교체**:
   - `## 2. 해외주식/미국주식 계좌` 헤딩부터 그 섹션이 끝나는 `## 3. 해외주식/미국주식 시세` 헤딩 직전까지를 codex-task §A.1 본문으로 교체.
   - `## 4. 모의투자 주문` 헤딩부터 그 섹션이 끝나는 `## 다음 작업 가이드` 헤딩 직전까지를 codex-task §A.2 본문으로 교체.
4. **추측 금지**. codex-task §A 본문 외 어떤 값도 catalog 에 추가하지 않는다.
5. **secret 보호**. 본문에 실제 자격증명 / 토큰 / 계좌번호 / Bearer 가 등장하지 않는다 (정책상 placeholder `${access_token}` 만 허용 — KIS_1 catalog 와 동일).
6. **검증**:
   - `git diff -- docs/kis/MISSING_OFFICIAL_VALUES.md` 가 §2 와 §4 두 섹션의 본문 교체만 포함. 다른 섹션 변동 0 줄.
   - `grep -n "Bearer eyJ\|appkey=\|appsecret=\|access_token=" docs/kis/MISSING_OFFICIAL_VALUES.md` 결과 0 줄.
   - `python -m compileall app tests` 통과 (코드 변경 없으므로 회귀 0). `pytest` 실행은 본 job 의 완료 기준이 아니나 Codex 가 안심하기 위해 실행해도 무방.
7. **patch.md** 작성: §A.3 의 양식 그대로.

## 5. 테스트 기준

본 job 은 문서 전용이므로 코드 테스트 실행은 완료 기준이 아니다. 그러나 회귀 안전을 위해 다음을 확인한다.

- `python -m compileall app tests` 통과 (필수, 코드 무변경 회귀).
- `pytest -p no:cacheprovider` 가 본 job 의 diff 와 무관하게 기존 350 passed 그대로 유지 (선택적 확인).
- 안전 grep:
  - `grep -n "appkey=\|appsecret=\|access_token=\|Bearer eyJ" docs/kis/MISSING_OFFICIAL_VALUES.md` → 0 줄.
  - `grep -n "12345678\|fake-key\|fake-secret" docs/kis/MISSING_OFFICIAL_VALUES.md` → 0 줄.
  - `grep -n "import requests\|import httpx\|import aiohttp\|import urllib3" docs/kis/MISSING_OFFICIAL_VALUES.md` → 0 줄.
- 6.xlsx 에 명시되지 않은 항목 (예: 외국 거래소 별 stale-quote 판단 기준, 일부 부가 응답 필드) 은 `<TBD>` 와 `Confirmed: no` 그대로 유지.

## 6. 리뷰 체크리스트

문서 정합성:

- [ ] §2 본문이 6.xlsx 의 5 개 paper-지원 endpoint (잔고 / 매수가능금액 / 체결기준 현재잔고 / 주문체결내역) + paper-미지원 4 개 endpoint (결제기준 잔고 / 일별거래내역 / 기간손익 / 해외증거금 통화별) 의 path / method / 실전 TR_ID / 모의 TR_ID / 모의 지원 여부를 한 표에 정리.
- [ ] §4 본문이 6.xlsx 의 paper-지원 endpoint (주문 / 정정취소 / 예약주문 접수 / 예약주문 취소) + paper-미지원 endpoint (미체결 / 예약주문조회 / 미국주간주문 / 미국주간정정취소 / 지정가주문번호 / 지정가체결내역) 의 path / method / 실전 TR_ID / 모의 TR_ID / 모의 지원 여부를 한 표에 정리.
- [ ] 모의투자에서 `ORD_DVSN=00 지정가` 외 주문구분이 지원되지 않는다는 사실이 §4 의 제약 sub-section 에 명시.
- [ ] 모의투자에서 `OVRS_EXCG_CD` 가 NASD / NYSE / AMEX 만 허용되고 (잔고 sheet 기준), 통화 코드는 USD / HKD / CNY / JPY / VND 가 허용된다는 사실이 catalog 에 들어감.
- [ ] 체결기준 현재잔고는 모의에서 `output3` 만 사용 가능하다는 공식 단서가 §2 에 들어감.
- [ ] 주문체결내역은 모의에서 `PDNO=""`, `SLL_BUY_DVSN="00"`, `CCLD_NCCS_DVSN="00"` 만 허용된다는 단서가 §4 에 들어감.
- [ ] 미체결 (`/inquire-nccs`) 은 모의 미지원 — 모의 TR_ID 칸이 `모의투자 미지원`.
- [ ] 모의 도메인 `https://openapivts.koreainvestment.com:29443` 와 실전 도메인 `https://openapi.koreainvestment.com:9443` 가 endpoint catalog 에 명시되며, 두 값은 KIS_1 의 `MISSING_MARKET_DATA_VALUES.md` 와 일치.

안전 회귀:

- [ ] §1 OAuth, §3 시세, "정책", "다음 작업 가이드", "보안" 섹션은 본문 변동 0 줄.
- [ ] `app/`, `tests/` 의 코드 / 테스트 변경 0건.
- [ ] `.env`, `.env.example` 변경 0건.
- [ ] 실 app key / app secret / 계좌번호 / access token / Bearer / refresh token 이 catalog 에 등장하지 않는다 (`grep` clean).
- [ ] 외부 HTTP 라이브러리 import 추가 0건.
- [ ] `OrderType.MARKET` 가드 / live trading 가드 / RiskEngine / OMS / PaperBroker 정책 변동 0건.
- [ ] `MISSING_MARKET_DATA_VALUES.md` 변경 0줄.
- [ ] 자동 git commit / push / merge / deploy 0건.

patch.md 정합성:

- [ ] 채워진 값 요약 (endpoint 단위) 포함.
- [ ] 모의 미지원 endpoint 목록 포함.
- [ ] 6.xlsx 에서 확인할 수 없어 `<TBD>` 로 남긴 항목 목록 포함 (예: stale quote 판단 기준 — 시세 catalog 의 §3 영역이므로 본 job 범위 외 가능).
- [ ] `api-account-001` (잔고 / 매수가능금액 / 체결기준 현재잔고 / 주문체결내역) 진행 가능 여부 판단.
- [ ] `api-orders-paper-001` (주문 / 정정취소 — `VTTT1002U`/`VTTT1001U`/`VTTT1004U`) 진행 가능 여부 판단.

자동화 금지:

- [ ] commit / push / merge / PR / deploy 가 수행되지 않았다.
- [ ] `.env` / secret / credential / API key / token 이 수정/노출되지 않았다.

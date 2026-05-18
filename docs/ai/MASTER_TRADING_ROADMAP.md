# 미국주식 자동 페이퍼매매 프로젝트 전체 마스터 플랜

작성 목적: Claude와 Codex가 더 이상 작은 단위로 중복 작업하지 않고, A~Z 전체 흐름을 공유한 상태에서 설계·구현·리뷰를 교차 진행하기 위한 기준 문서입니다.

---

## 0. 지금 방식의 문제

지금까지의 문제는 코드 자체보다 작업 방식에 있습니다.

- KIS 실제 HTTP 연결, dry-run, dashboard, `.env` 로딩, status 확인이 서로 연결된 큰 그림 없이 따로 진행되었습니다.
- KIS 공식 문서값이 없는 상태에서 "실제 HTTP 구현"을 여러 번 요청해서 Codex가 계속 fail-closed/TODO로 멈췄습니다.
- dry-run은 돌아가지만 실제 시세 기반 후보 생성이 안 되어 `candidates_seen=0` 상태가 반복되었습니다.
- UI는 생겼지만 실제 사용자가 확인해야 할 흐름이 아직 완전히 정리되지 않았습니다.
- mvp 번호와 실제 완료 상태가 섞여서 같은 작업을 두 번 하는 상황이 생겼습니다.

이제부터는 작은 작업을 계속 던지는 방식이 아니라, 전체 로드맵을 Claude가 먼저 분석하고, Codex가 단계별 구현을 진행하며, 각 단계가 끝날 때마다 Claude가 리뷰하는 구조로 진행합니다.

---

## 1. 최종 목표

최종 목표는 다음입니다.

> 미국주식 변동성 높은 종목을 대상으로 실제 시장 데이터 기반 자동 페이퍼매매 시스템을 만들고, 충분한 모의투자 검증을 통해 전략의 승률, 손익비, 최대 낙폭, 체결 품질, 스프레드 영향, 슬리피지 가능성을 분석한 뒤, 기준을 만족할 경우에만 소액 live validation을 검토한다.

핵심 원칙:

- 처음부터 실전매매를 하지 않는다.
- 실제 시장 데이터를 사용한다.
- 실제 주문 전에는 반드시 KIS 모의투자 / paper trading으로 충분히 검증한다.
- LLM은 매수/매도 판단자가 아니다.
- LLM은 설계, 리뷰, 분석, 코드 보조 역할만 한다.
- 실시간 주문 판단은 코드 기반 전략, RiskEngine, OMS가 수행한다.
- 모든 주문은 `Strategy → RiskEngine → OMS → BrokerAdapter → KIS` 경로를 지나야 한다.
- Strategy, Agent, LLM은 KIS를 직접 호출하면 안 된다.
- 시장가 주문은 기본 금지한다.
- 지정가 주문 중심으로 설계한다.
- live trading은 기본 비활성이다.
- live validation은 별도 단계에서 preflight, arm, whitelist, 소액 제한, kill switch를 모두 통과해야만 가능하다.

---

## 2. 현재까지 완료된 축

### 2.1 AI 개발팀 / GUI 작업 시스템

- Claude + Codex 2-role 구조로 단순화
- GUI에서 한국어 요청 입력
- Claude 계획 생성
- Codex 구현 실행
- Claude 리뷰 실행
- 기존 5-role 구조 deprecated
- tmux / GUI / patch.md / review.md 기반 작업 기록 구조 마련

### 2.2 paper-trading 프로젝트 기본 구조

- `projects/paper-trading` 생성
- FastAPI 서버 실행 가능
- `/docs` 작동
- `/paper/status` 작동
- `/paper/dry-run/status` 작동
- `/dashboard` UI 추가
- `.env` 파일 존재
- `.env` key 이름 문제 수정 후 KIS config 로딩 성공
- `secret_exposed=false` 확인
- `live_enabled=false` 확인
- `market_orders_allowed=false` 확인
- `kis_order_dry_run=true` 확인

### 2.3 전략 / 리스크 / 주문 경계

- 프리마켓 갭 + 거래량 돌파 전략 구현
- RiskEngine 기본 구조
- OMS 기본 구조
- BrokerAdapter 경계
- PaperBroker / KisBroker skeleton
- Strategy가 직접 Broker를 호출하지 않는 구조
- Agent/LLM이 직접 주문하지 않는 원칙 유지
- 주문은 RiskEngine/OMS를 거쳐야 한다는 구조 유지

### 2.4 KIS 관련 현재 상태

완료된 것:

- KIS config 구조
- `.env` 기반 KIS 설정 로딩
- KIS account masking
- `kis_config_loaded=true`
- `account_no_masked=***xxxx`
- `secret_exposed=false`
- KIS Auth / Account / MarketData / Order skeleton
- KIS dry-run/fail-closed 구조
- KIS_ORDER_DRY_RUN=true 기본값
- 실제 endpoint/TR ID/payload 추측 금지 원칙

아직 안 된 것:

- KIS 실제 OAuth HTTP 인증
- KIS 실제 계좌/잔고/포지션 조회
- KIS 실제 해외주식/미국주식 시세 조회
- KIS 실제 모의투자 주문 HTTP 전송
- KIS 미체결/체결/정정/취소 실제 연결
- 실제 시세 기반 후보 생성

### 2.5 dry-run / 리포트

완료된 것:

- dry-run runner
- dry-run status
- dashboard에서 dry-run 상태 확인
- dry-run tick 실행 가능
- dry-run report analyzer
- `analysis_summary.json`
- `analysis_report.md`
- `claude_review_input.md`
- secret 노출 방지
- 테스트 다수 통과

현재 한계:

- 실제 시세 데이터가 없으므로 `candidates_seen=0`
- 실제 모의투자 주문이 아니고 dry-run/order preview 단계
- 분석할 후보/주문 데이터가 거의 없음

---

## 3. 지금 가장 큰 병목

현재 가장 큰 병목은 KIS 주문이 아니라 **실제 시장 데이터 입력**입니다.

현재 시스템은 dry-run 구조와 dashboard, analyzer까지 있지만, 실제 시세/호가/거래량이 들어오지 않아서 전략 후보가 생성되지 않습니다.

따라서 다음 작업 우선순위는 다음입니다.

1. KIS 실제 시세 조회 연결
2. 실제 시세 기반 후보 생성
3. 후보 → 전략 → RiskEngine → OMS → dry-run 주문 흐름 검증
4. KIS 모의투자 주문 연결
5. 장시간 모의투자 검증
6. 결과 리포트 / 승률 / 손익비 분석
7. 소액 live validation 준비

KIS 모의투자 주문 HTTP를 먼저 붙여도, 실제 시세와 후보가 없으면 검증할 수 없습니다. 따라서 KIS 시세 조회가 주문 연결보다 먼저입니다.

---

## 4. 새 로드맵

기존 번호 혼선을 여기서 정리합니다.

### mvp-023: KIS 실제 시세 조회 연결

목표:

- KIS Open API를 통해 미국주식/해외주식 현재가 또는 quote 데이터를 가져오는 경계를 실제로 연결한다.
- 공식 문서에 근거한 endpoint/TR ID/payload만 사용한다.
- 공식 문서값이 없으면 `docs/kis/MISSING_MARKET_DATA_VALUES.md`에 필요한 값을 기록하고 fail-closed한다.

필수 산출물:

- KIS quote client
- `get_quote(symbol)`
- `get_last_price(symbol)`
- bid/ask/last/volume/timestamp 모델
- stale quote 판단
- spread 계산
- `/paper/status` 또는 `/dashboard`에 market data 상태 표시
- quote 조회 테스트

완료 기준:

- 특정 심볼에 대해 실제 또는 공식 문서 기반 quote 조회 구조가 완성된다.
- 공식 문서값이 부족하면 fail-closed + 필요한 문서값 목록이 명확히 남는다.
- secret/account/token이 노출되지 않는다.
- 기존 테스트가 통과한다.

---

### mvp-024: 실제 시세 기반 종목 후보 생성

목표:

- 실제 시세/거래량/스프레드 기반으로 전략 후보를 만든다.
- 처음에는 종목 universe를 작게 시작한다.
- 예: `SYMBOL_ALLOWLIST=AAPL,TSLA,NVDA,AMD,PLTR`
- 프리마켓 갭 전략에 필요한 입력을 생성한다.

필수 산출물:

- symbol universe config
- quote snapshot model
- candidate scanner
- premarket gap candidate builder
- spread filter
- volume filter
- stale quote filter
- dashboard에 candidates_seen 표시
- 후보 생성 테스트

완료 기준:

- dry-run tick 실행 시 `candidates_seen`이 0이 아닌 상태를 만들 수 있다.
- 후보가 strategy로 전달된다.
- blocked/pass 사유가 기록된다.
- 실제 주문은 나가지 않는다.

---

### mvp-025: 후보 → 전략 → RiskEngine → OMS → dry-run 주문 흐름 검증

목표:

- 실제 후보가 전략과 리스크를 통과하거나 차단되는지 확인한다.
- RiskEngine 차단 사유를 정리한다.
- OMS로 넘어가는 후보와 거절되는 후보를 분리한다.
- KIS_ORDER_DRY_RUN=true 상태에서 dry-run order preview만 생성한다.

필수 산출물:

- 후보별 decision trace
- risk verdict
- oms accepted/rejected counters
- dry-run order preview
- dashboard에서 후보/차단/주문 preview 확인
- 리포트에 block reason 반영

완료 기준:

- Tick 1회 실행 후 `candidates_seen`, `candidates_blocked`, `candidates_passed_risk` 값이 의미 있게 나온다.
- RiskEngine/OMS 경계가 유지된다.
- Strategy/Agent/LLM이 직접 주문하지 않는다.
- 실제 주문은 나가지 않는다.

---

### mvp-026: KIS 모의투자 주문 연결

목표:

- KIS 공식 문서값을 기반으로 KIS 모의투자 지정가 주문을 실제 연결한다.
- 여전히 live trading은 비활성이다.
- 실전 주문은 금지한다.
- KIS_ENV=paper에서만 허용한다.
- 기본은 dry-run true이고, 모의투자 전송은 명시적으로 dry-run false일 때만 가능하다.

필수 산출물:

- KIS paper `place_order`
- `cancel_order`
- `replace_order`
- `get_open_orders`
- `get_fills`
- `get_order_status`
- broker_order_id 저장
- sanitized raw response
- KIS paper order integration tests

완료 기준:

- KIS 모의투자 환경에서만 주문 가능
- 시장가 주문 거절
- live trading true면 거절
- KIS_ENV != paper면 거절
- account/secret/token 노출 없음
- OMS/RiskEngine 경계 유지

---

### mvp-027: 장시간 모의투자 검증

목표:

- 실제 시세 기반으로 일정 시간 이상 paper/dry-run 또는 KIS 모의투자를 돌린다.
- 오류, stale quote, 스프레드, 후보 생성, 주문 preview/모의주문, 체결/미체결을 기록한다.

필수 산출물:

- long-run runner
- session-aware run schedule
- start/stop/resume
- error threshold
- auto stop
- dashboard long-run 상태
- report files

완료 기준:

- 최소 몇 시간 동안 안정적으로 실행된다.
- 에러가 기록된다.
- 중단/재시작 가능하다.
- secret 노출 없음.
- 실제 live trading 없음.

---

### mvp-028: 결과 리포트 / 승률 / 손익비 분석

목표:

- dry-run / paper trading 결과를 분석한다.
- 단순 승률이 아니라 기대값, 손익비, 최대 낙폭, 연속 손실, 체결 가능성, 스프레드 영향을 본다.

필수 산출물:

- win rate
- average win/loss
- profit factor
- expectancy
- max drawdown
- consecutive losses
- by-symbol stats
- by-session stats
- by-strategy stats
- spread/slippage sensitivity
- Claude review input
- strategy improvement recommendations

완료 기준:

- 실제 전략 개선에 사용할 수 있는 리포트가 나온다.
- 단순 "수익"이 아니라 리스크까지 평가된다.
- 개선안이 Codex 작업으로 이어질 수 있다.

---

### mvp-029: 소액 live validation 준비

목표:

- paper trading 결과가 충분히 좋을 때만 소액 live validation을 준비한다.
- 실제 live trading은 여전히 기본 비활성이다.
- 버튼/preflight/arm/whitelist/notional limit이 있어야 한다.

필수 산출물:

- live validation preflight
- live arm/disarm
- allowed_symbols
- max_order_notional
- max_daily_notional
- max_orders_per_day
- live-only kill switch
- auto-disarm on drift/error
- audit log
- dashboard 표시

완료 기준:

- live는 기본적으로 절대 실행되지 않는다.
- 사람이 명시적으로 arm해야 한다.
- 모든 조건 미충족 시 fail-closed.
- 실전 확대 전 소액 검증만 가능.

---

## 5. 중복 방지 규칙

앞으로 아래 작업은 공식 문서값 없이 다시 실행하지 않습니다.

- KIS OAuth 실제 HTTP 구현
- KIS 계좌/잔고/포지션 실제 조회
- KIS 시세 실제 조회
- KIS 모의투자 주문 HTTP 구현

공식 문서값이 없으면 Codex는 구현하지 말고 다음만 해야 합니다.

1. 필요한 공식 문서값 목록 작성
2. fail-closed 유지
3. 테스트 유지
4. patch.md에 명확히 기록

앞으로 "KIS 실제 연결" 작업을 요청할 때는 반드시 아래 정보 중 해당하는 값을 포함해야 합니다.

- base URL
- endpoint path
- method
- headers
- request body/query fields
- TR ID
- response fields
- paper/live 구분
- 공식 문서 출처

---

## 6. Claude와 Codex 협업 방식

### Claude 역할

Claude는 다음을 수행합니다.

1. 전체 로드맵 유지
2. 중복 작업 감지
3. 이번 작업이 어느 mvp에 해당하는지 판단
4. Codex가 구현할 수 있는 명확한 codex-task.md 작성
5. 공식 문서값이 없는 작업은 막기
6. 구현 후 리뷰
7. 안전성 검토
8. 다음 단계 제안

Claude는 코드를 무작정 수정하지 않습니다.

### Codex 역할

Codex는 다음을 수행합니다.

1. Claude가 승인한 codex-task.md만 구현
2. 작업 범위를 확장하지 않음
3. 테스트 추가/수정
4. compileall/pytest 실행
5. patch.md 작성
6. secret 노출 방지
7. live trading 활성화 금지
8. endpoint/TR ID 추측 금지

Codex는 commit/push/merge를 하지 않습니다.

### 사용자 역할

사용자는 다음을 수행합니다.

1. 큰 방향 결정
2. KIS 공식 문서값 제공
3. .env 값 직접 관리
4. 최종 커밋 판단
5. 실제 live validation 여부 결정
6. 실거래 전 마지막 승인

---

## 7. Claude에게 줄 마스터 프롬프트

```text
Use prompts/claude.md.

Project directory: /root/ai-dev-center/projects/ai-team

Read the current paper-trading project and the AI job history.

Important context:
The user is frustrated because work has been repeated in small MVP chunks, especially around KIS HTTP integration.
From now on, maintain the master roadmap below and prevent duplicate work.

Master roadmap:
- mvp-023: KIS actual market data / quote connection
- mvp-024: real market data based candidate generation
- mvp-025: candidate -> strategy -> RiskEngine -> OMS -> dry-run order flow verification
- mvp-026: KIS paper order integration
- mvp-027: long-running paper trading verification
- mvp-028: performance report / win rate / expectancy analysis
- mvp-029: small live validation preparation

Before creating a new codex-task:
1. Check whether the requested work already exists.
2. Check previous docs/ai/jobs.
3. Do not repeat mvp-011~017 KIS HTTP attempts without official KIS endpoint/TR ID/payload values.
4. If official values are missing, write a missing-values task instead of fake implementation.
5. Prefer fewer, larger but reviewable work packages.
6. Keep the user-facing workflow simple.

Current important state:
- /dashboard works.
- KIS config loads from .env.
- kis_config_loaded=true.
- account_no_masked works.
- secret_exposed=false.
- dry-run runner exists.
- analyzer exists.
- candidates_seen is still 0 because real market data / candidate generation is missing.

Next recommended job:
mvp-023: KIS actual market data / quote connection.

Your task:
Analyze the current code and create a plan.md and codex-task.md for mvp-023.
Do not let Codex invent KIS endpoints or TR IDs.
If required official KIS document values are missing, codex-task.md must instruct Codex to create docs/kis/MISSING_MARKET_DATA_VALUES.md and keep fail-closed behavior.

Output:
- current state summary
- already completed work
- duplicate work to avoid
- mvp-023 scope
- files likely to change
- Codex implementation instructions
- test criteria
- review checklist
```

---

## 8. mvp-023 기본 작업 요청

```markdown
# 작업 ID
mvp-023

# 작업명
KIS 실제 시세 조회 연결

현재 시스템은 대시보드, dry-run, report analyzer는 작동하지만 실제 시장 데이터가 없어서 candidates_seen=0 상태다.

목표:
KIS Open API 공식 문서값이 확인되는 범위에서 미국주식/해외주식 실제 시세 조회를 연결하고, 전략 후보 생성의 입력 데이터로 사용할 수 있게 준비한다.

중요:
- KIS endpoint/TR ID/payload를 추측하지 마.
- 공식 문서값이 없으면 실제 HTTP 구현하지 말고 docs/kis/MISSING_MARKET_DATA_VALUES.md에 필요한 값을 정리해.
- live trading은 계속 비활성.
- 시장가 주문 금지.
- 실주문 기능 건드리지 마.
- Strategy가 KIS 직접 호출하지 마.
- BrokerAdapter/MarketDataClient 경계를 유지해.
- secret/account/token 노출 금지.

완료 기준:
- get_quote(symbol) 또는 동등한 quote 조회 경계가 명확하다.
- 공식 문서값이 있으면 실제 HTTP 연결.
- 공식 문서값이 없으면 fail-closed + missing docs.
- quote model에 last, bid, ask, volume, timestamp, stale 여부가 있다.
- spread 계산 가능.
- 테스트 통과.
- 다음 mvp-024에서 candidate scanner가 이 quote를 사용할 수 있다.

추가 조건:
- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
- 필요한 경우에만 최소한의 질문을 해.
```

---

## 9. 저장 위치

이 문서는 아래 경로에 저장하는 것을 추천합니다.

```text
docs/ai/MASTER_TRADING_ROADMAP.md
```

모든 새 작업 전에 Claude가 이 문서를 읽게 합니다.

Codex는 해당 작업의 `codex-task.md`만 읽습니다.

---

## 10. 현재 상태 (roadmap-status-fix, 2026-05-15)

상세 진행 현황은 [`docs/ai/ROADMAP_STATUS.md`](ROADMAP_STATUS.md)에 단일 source of truth로 보관합니다. 본 섹션은 요약입니다.

### 10.1 Roadmap slot 상태

| Slot | 상태 | 비고 |
| --- | --- | --- |
| mvp-023 KIS 시세 조회 | ⏳ **BLOCKED-BY-DOCS** | Quote 도메인 + mapper skeleton + MISSING_MARKET_DATA_VALUES catalog 완료. HTTP만 공식값 대기. |
| mvp-024 후보 생성 | ⏸️ 미시작 | mvp-023 unblock 또는 synthetic source 시작 |
| mvp-025 dry-run flow 검증 | ⏸️ 미시작 | mvp-024 필요 |
| mvp-026 KIS 모의투자 주문 | ⏸️ 미시작 (BLOCKED-BY-DOCS 예상) | `MISSING_OFFICIAL_VALUES.md` §4 채워야 unblock |
| mvp-027 장시간 검증 | ⏸️ 미시작 | mvp-024..026 후 |
| mvp-028 성과 분석 | ⏸️ 미시작 | mvp-027 후 |
| mvp-029 live validation prep | ⏸️ 미시작 | 모든 이전 단계 + 명시적 사용자 승인 |

### 10.2 Foundation (mvp-001..mvp-022) 요약

paper-trading 골격, KIS 설정/skeleton, dry-run runner, analyzer, helper scripts, dashboard UI, `.env` 자동 로딩 모두 완료. **pytest 214 passed**. 안전 불변식(live 6단 차단 / OrderType MARKET 부재 / HTTP 라이브러리 import 0건 / KIS endpoint 0건 / raw credentials 노출 0건)이 누적 유지됨.

### 10.3 mvp-023 분류

**BLOCKED-BY-DOCS** — 완료 아님, 폐기 아님. 부분 산출물(Quote 도메인 모델, mapper skeleton, MISSING_MARKET_DATA_VALUES catalog)은 보존. HTTP 호출 부분만 미완료. **사용자가 `docs/kis/MISSING_MARKET_DATA_VALUES.md`의 `<TBD>` 항목을 KIS 공식 개발자 포털에서 채우면** 같은 mvp-023 슬롯 안에서 HTTP 부분 재개. **새 mvp 번호로 이동하지 않음.**

### 10.4 다음 단 하나의 작업

**사용자 액션: `docs/kis/MISSING_MARKET_DATA_VALUES.md`의 `<TBD>` 항목을 채운다.**

채우기 어려운 경우 차선: mvp-024를 `source="synthetic"` mock 데이터로 시작 (반드시 "로컬 검증용 — KIS 실제 HTTP 대체 아님"으로 표시).

---

## 11. 중복 방지 규칙 (필수)

### 11.1 새 mvp 번호 생성 금지 원칙

앞으로 새 작업이 필요하면 다음 순서로 처리합니다.

1. **`ROADMAP_STATUS.md`와 본 문서 §4의 mvp-023..mvp-029 slot 중 하나에 매핑** 시도.
2. 매핑할 slot이 없으면 본 문서 §4를 먼저 수정하여 slot을 추가/수정.
3. **새 번호(mvp-024-1, mvp-024-fix, mvp-030 등) 생성 금지.**
4. BLOCKED 상태는 새 번호 대신 BLOCKED 표시 + 재개 조건을 같은 slot 안에 명시.

### 11.2 Codex 구현 지시 생성 전 필수 점검

Claude가 새 codex-task.md를 만들기 전:

- [ ] `ROADMAP_STATUS.md`에서 해당 slot 상태 확인.
- [ ] 본 문서 §4에서 slot 정의 확인.
- [ ] `docs/ai/jobs/<slot>/` 폴더에서 기존 plan/codex-task/patch/review 확인.
- [ ] 중복이면 새 작업 만들지 말고 기존 자료 업데이트.
- [ ] 공식 KIS 문서값 없는 KIS HTTP 작업이면 작성 금지 (BLOCKED 표시).

### 11.3 mock/synthetic 데이터 명명 규칙

mock/synthetic 데이터 사용 시:

- 패키지/모듈 이름에 `synthetic` 또는 `mock` 명시.
- `Quote.source` 필드를 `"synthetic"`/`"mock"`으로 명시.
- 문서에 **"로컬 검증용 — KIS 실제 HTTP 대체 아님"** 명시.
- `/paper/status`에 데이터 source flag 표시.
- 향후 실 KIS 데이터 land 시 source 교체로 마이그레이션.

### 11.4 KIS HTTP 시도 반복 금지

본 저장소에서 다음 작업은 공식 KIS 문서값 없이 다시 실행하지 않습니다.

- KIS OAuth 실제 HTTP 구현
- KIS 계좌/잔고/포지션 실제 조회
- KIS 시세 실제 조회
- KIS 모의투자 주문 HTTP 구현
- KIS 미체결/체결/주문 상태 실제 조회

해당 영역의 신규 작업 요청 시 반드시 다음 정보가 포함되어야 합니다.

- base URL
- endpoint path
- HTTP method
- required headers
- request body/query fields
- TR ID (모의투자용)
- response field 이름
- paper/live 구분
- KIS 공식 문서 출처

위 정보가 미확정이면 Claude는 codex-task.md 대신 `MISSING_*_VALUES.md` catalog 업데이트만 지시합니다.

### 11.5 안전 불변식 (모든 신규 작업이 보존해야 함)

- `OrderType.MARKET` 추가 금지.
- live trading 활성화 코드 경로 신설 금지.
- 외부 HTTP 라이브러리(`requests`/`httpx`/`aiohttp`/`urllib3`) import 신설 금지(KIS endpoint 확정 + 별도 mvp 진입 시점에 결정).
- raw KIS app key / app secret / 계좌번호 / token이 코드/문서/응답/log 어디에도 미노출.
- `Settings`의 비밀 필드 `field(repr=False)` 유지. `KisBroker`/sub-client `__repr__` masking 유지.
- Strategy 패키지가 `app.broker.kis*` import 금지.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- LLM/Agent가 KIS 또는 BrokerAdapter를 직접 호출하지 않음.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지.
- `pip install` 자동 실행 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.

---

이 §10–11은 roadmap-status-fix(2026-05-15)에서 추가됨. 이후 진행 현황은 `ROADMAP_STATUS.md`를 우선 갱신하고, 큰 슬롯 변경 시 본 문서도 동기화.

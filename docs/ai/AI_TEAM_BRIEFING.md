# AI Team Briefing — Paper Trading Project (2026-05-18 시점)

본 문서는 본 프로젝트의 현재 상태와 안전 규칙을 다른 LLM(예: ChatGPT)에 전달해 **다음 job용 한국어 요청을 작성**하도록 돕는 컨텍스트 패키지다. 코드 본문은 포함하지 않고, 의사결정에 필요한 사실만 정리한다.

---

## 1. 프로젝트 한 줄 요약

한국투자증권 KIS Open API + 자체 paper trading 엔진을 조합해, **모의투자(paper) 기반 자동매매 시뮬레이션**을 만드는 단일 저장소. 라이브 트레이딩은 영구 비활성. 모든 변경은 Claude(설계/리뷰) + Codex(구현) 두 AI 역할 워크플로로 진행.

저장소: `/root/ai-dev-center/projects/ai-team` (단일 git repo, branch `feat/job-006-control-center-upgrade`).
주요 서브프로젝트: `projects/paper-trading/` (Python 3.12, venv at `.venv`, stdlib + dotenv만 사용).

---

## 2. AI 워크플로 (필독)

```
사람 작성 한국어 요청 (request.ko.md)
      ↓
Claude: 계획·아키텍처·리뷰 (plan.md / codex-task.md / review.md)
      ↓
Codex: 구현·테스트·요약 (코드 변경 + patch.md)
      ↓
Claude: diff + patch.md 리뷰 (review.md에 APPROVE / REQUEST CHANGES / BLOCK)
      ↓
사람: git status/diff 확인 후 직접 staging/commit
```

핵심 디렉터리: `docs/ai/jobs/{JOB_ID}/{request.ko.md, plan.md, codex-task.md, patch.md, review.md, status.md}`.

**자동화하지 않는 것**: `git commit`, `git push`, PR merge, production 배포, `.env` 수정, auth/payment/infra 변경, DB migration, live trading 활성화, broker 실주문 생성.

---

## 3. 작업 완료 상태 (commit된 또는 워크트리 land된)

### 인프라/스캐폴딩 (commit됨)

- **mvp-001 ~ mvp-022**: `Settings`, `Strategy`/`OMS`/`RiskEngine`/`PortfolioService`/`PaperBroker` 골격, dry-run controller, 자동 `.env` 로딩, GUI 일부.
- **mvp-023**: `Quote` 도메인 모델(broker-agnostic, frozen, spread_pct/is_stale 메서드). KIS quote mapper skeleton (NotImplementedError, fail-closed).
- **KIS_1**: `docs/kis/MISSING_MARKET_DATA_VALUES.md` catalog — 사용자 업로드 KIS 공식 자료 기반으로 endpoint/TR ID/응답 필드/거래소 코드/세션 정보 모두 `Confirmed: yes`로 채움. **Option B 정책 채택**: 시세(read-only)는 실전 도메인 허용, 주문/계좌는 모의 전용.
- **api-auth-001**: KIS OAuth (`POST /oauth2/tokenP`, `/oauth2/revokeP`) + 안전 HTTP 래퍼 + 토큰 캐시. 3-모드(`mock`/`paper`/`live`). live 모드는 본 job에서 fail-closed. stdlib only (urllib.request).
- **paper-001 (방금 APPROVE)**: 내부 paper trading MVP 확장판 land 준비 완료 (워크트리, commit은 사람 직접). 6개 기능:
  - LIMIT / STOP_LIMIT / **MARKET** 시뮬레이션 (MARKET은 3중 가드 통과 시만)
  - **Partial fill** (volume 비율 기반)
  - **Quote staleness** 검사 in `PaperBroker.tick()`
  - **Session 검사** (`Quote.session`이 `_allowed_sessions`에 없으면 fill 0건; None은 backward-compat 허용)
  - **Cash + Realized/Unrealized PnL** (`PaperAccount`/`PaperJournal`/`PaperEngine`)
  - **Multi-currency** (`PaperAccount.cash: dict[currency, Decimal]`, FX 변환 없음)
- 303 tests PASS. 안전 grep 6/6 clean.

### 워크트리에 있고 commit 대기 중

- paper-001 변경 (~25 files), 위 review.md의 staging 블록 참고.

---

## 4. 절대 안전 규칙 (모든 새 job에 자동 상속)

1. **paper가 기본**. 모든 새 코드는 `Settings.trading_mode = TradingMode.PAPER` + `live_trading_enabled = False`에서만 동작.
2. **Live trading 영구 비활성**. live 경로는 `load_settings()`에서 reject(`"Phase 1 only supports paper trading"`, `"Live trading is disabled in Phase 1"`).
3. **LLM/Agent는 executable order 못 만듦**. 추천 agent는 `OrderIntent`(non-executable)만 생성. `BrokerOrder` 생성은 OMS만.
4. **모든 주문은 Strategy → RiskEngine → OMS → PaperBroker 통과**. 이 체인을 우회하는 새 경로 금지.
5. **OrderType.MARKET 3중 가드**: `ALLOW_PAPER_MARKET_ORDERS=true` AND `TradingMode.PAPER` AND `live_trading_enabled=False`. 하나라도 깨지면 RiskEngine reject. 기본 `ALLOW_PAPER_MARKET_ORDERS=false`.
6. **`ALLOW_MARKET_ORDERS=true`는 `load_settings()`에서 즉시 reject**. 이건 별 flag, 절대 풀리지 않음.
7. **실 broker API 호출은 broker adapter 안에만**. `KisBroker`, `KisMarketDataClient`, `KisAccountClient` 본문은 현재 모두 `NotImplementedError`로 fail-closed.
8. **`KisHttpClient`/`SafeKisHttpClient`는 OAuth tokenP/revokeP만 호출 가능**(path allowlist). 그 외 path는 `KisHttpError`로 reject.
9. **외부 HTTP 라이브러리 금지**. `requests`/`httpx`/`aiohttp`/`urllib3` import 0건. stdlib `urllib.request`만 허용.
10. **`.env` 읽기/수정 금지**. dotenv가 자동 로드만 함. `.env.example`은 변수 이름 + 한 줄 설명만 (값 0건).
11. **실 app key / app secret / access token / 계좌번호 / Bearer 토큰 어디든 기록 금지**. 테스트는 `"fake-*"` 또는 8자리 이하 fake 숫자만.
12. **FX 변환 0건**. multi-currency는 통화별 분리 보관·보고만. `equity_total_in_base_currency`, `to_base_currency`, `exchange_rate` 같은 함수/상수 도입 금지.
13. **`OrderType.STOP`(stop without limit) 부재 유지**. LIMIT, STOP_LIMIT, MARKET 3개만.
14. **자동 git commit/push/merge/deploy 금지**. 사람이 직접 실행.

---

## 5. 디렉터리 구조 (핵심만)

```
projects/paper-trading/
├── app/
│   ├── api/{server.py, routes.py}        # FastAPI GUI 백엔드. paper-001 범위 외 통상 미접촉
│   ├── broker/
│   │   ├── base.py                       # BrokerAdapter Protocol
│   │   ├── paper.py                      # PaperBroker (tick으로 fill 시뮬레이션)
│   │   ├── alpaca_paper.py               # 별 paper broker
│   │   ├── kis.py                        # KIS skeleton, 대부분 NotImplementedError
│   │   ├── kis_http.py                   # SafeKisHttpClient (mock/paper/live mode)
│   │   ├── kis_token_cache.py            # InMemory + File token cache
│   │   └── kis_quote_mapper.py           # KIS raw quote → Quote (현재 NotImplementedError)
│   ├── config.py                         # Settings (frozen dataclass) + load_settings
│   ├── domain/
│   │   ├── enums.py                      # TradingMode/Side/OrderType/Session
│   │   ├── orders.py                     # OrderIntent/Order/BrokerOrder/OrderAck
│   │   ├── quote.py                      # Quote (broker-agnostic, spread_pct, is_stale)
│   │   ├── fills.py                      # Fill (paper-001)
│   │   └── market.py                     # StrategyInput
│   ├── oms/manager.py                    # OMS.place(intent) — risk → BrokerOrder → broker
│   ├── portfolio/
│   │   ├── service.py                    # PortfolioService (positions, PnL)
│   │   └── account.py                    # PaperAccount (cash ledger only, paper-001)
│   ├── risk/engine.py                    # RiskEngine.evaluate(intent)
│   ├── runtime/
│   │   ├── paper_runner.py               # 단순 Strategy→OMS 러너 (기존)
│   │   ├── dry_run.py                    # 장시간 동기 dry-run controller
│   │   ├── dry_run_report.py             # dry-run 리포트
│   │   ├── paper_engine.py               # 신규 (paper-001) — on_quote 처리
│   │   └── paper_journal.py              # 신규 (paper-001) — order/trade log
│   ├── strategy/                         # PremarketGap 전략 + Strategy Protocol
│   ├── session/, reports/, static/       # GUI dashboard 등 (paper-001 범위 외)
│   └── main.py                           # FastAPI entrypoint
├── tests/                                # pytest, 현재 303 PASS
└── .venv/                                # python -m venv

docs/
├── ai/
│   ├── CLAUDE_CODEX_WORKFLOW.md          # 워크플로 문서
│   ├── MASTER_TRADING_ROADMAP.md         # 전체 로드맵
│   ├── jobs/                             # 작업 폴더 (mvp-*, KIS_*, api-auth-*, paper-*)
│   └── AI_TEAM_BRIEFING.md               # 본 문서
└── kis/
    ├── MISSING_MARKET_DATA_VALUES.md     # 시세 catalog (KIS_1 land, Confirmed: yes)
    └── MISSING_OFFICIAL_VALUES.md        # OAuth/계좌/주문 catalog (§1 OAuth는 api-auth-001로 land, §2-§4 미land)

prompts/
├── claude.md                             # Claude role prompt (Planner+Architect+Reviewer)
└── codex-implementer.md                  # Codex role prompt (Implementer)

uploads/1..6.xlsx                          # KIS 공식 API spec exports (참고용, commit됨)
```

---

## 6. Settings (환경변수) 현재 상태

```
TRADING_MODE              # paper (live는 load_settings reject)
LIVE_TRADING_ENABLED      # false (true면 reject)
PAPER_STARTING_CASH       # 100000
MAX_ORDER_NOTIONAL_USD    # 5000
MAX_OPEN_POSITIONS        # 20
SYMBOL_ALLOWLIST          # 비어있음
STRATEGY_PREMARKET_*      # 전략 파라미터들
ALLOW_MARKET_ORDERS       # false (true면 load_settings reject — 절대 풀리지 않는 flag)
KILL_SWITCH_ENGAGED       # false

# KIS (mvp-014~api-auth-001)
KIS_ENV                   # paper / live (live는 SafeKisHttpClient 생성 자체가 fail-closed)
KIS_APP_KEY / KIS_APP_SECRET / KIS_ACCOUNT_NO
KIS_ORDER_DRY_RUN         # true 기본
KIS_API_MODE              # mock / paper / live (mock 기본; live 차단)
KIS_BASE_URL_PAPER        # https://openapivts.koreainvestment.com:29443
KIS_BASE_URL_LIVE         # 정의만 존재, 사용 경로 차단
KIS_OAUTH_TIMEOUT_SECONDS / KIS_OAUTH_MAX_RETRIES / KIS_TOKEN_EXPIRY_SAFETY_SECONDS / KIS_TOKEN_CACHE_PATH

# paper-001
ALLOW_PAPER_MARKET_ORDERS                  # false 기본 — 3중 가드 첫 단계
PAPER_COMMISSION_PER_SHARE                 # 0.005 기본
PAPER_COMMISSION_PER_FILL                  # 0 기본
PAPER_LOG_DIR                              # 미설정이면 메모리 only journal
PAPER_MAX_QUOTE_AGE_SECONDS                # 60 기본
PAPER_ALLOWED_SESSIONS                     # "regular" 기본
PAPER_MAX_FILL_RATIO_OF_VOLUME             # 0.05 기본 (5%)
PAPER_STARTING_CASH_BY_CURRENCY            # "USD=100000,KRW=130000000" 같은 multi-currency 명시
PAPER_BASE_CURRENCY                        # "USD" 기본
```

`.env`는 gitignored. `.env.example`만 commit됨.

---

## 7. 현재 NotImplementedError로 막혀 있는 곳 (다음 job 후보 영역)

- `KisAuthClient.authenticate()` — `KIS_API_MODE=paper`이면 동작, `mock`이면 즉시 fail-closed (구현됨).
- `KisAuthClient.refresh_token()`, `revoke()` — 작동.
- `KisAccountClient.get_account()` / `get_positions()` / `get_cash_balance()` — 모두 `NotImplementedError`.
- `KisMarketDataClient.get_quote()` / `get_last_price()` / `healthcheck_market_data()` — 모두 `NotImplementedError`.
- `KisBroker.place_order()` / `cancel_order()` / `replace_order()` / `get_open_orders()` / `get_fills()` / `get_order_status()` — 본문 미구현, `KIS_ORDER_DRY_RUN=true` + `validate_kis_order_request` pre-flight만.
- `kis_quote_mapper.kis_raw_quote_to_domain()` — `NotImplementedError`.
- `PaperEngine.submit_intents()` — 미구현 (paper-001에서 누락, follow-up 후보).

---

## 8. 다음 job 후보 (우선순위 순서)

1. **paper-001 commit 후 정리** — 사람이 직접 git staging/commit. 이미 review APPROVE.
2. **paper-001-gui** — 대시보드(`app/api/routes.py`, `app/static/dashboard.html`)에 `PaperAccount.cash`/`PaperJournal.trades`/`Snapshot.realized_pnl_by_currency`/`Snapshot.unrealized_pnl_by_currency` 노출. (현재 routes.py는 단일 Decimal만 표시.)
3. **api-market-data-001** — `KisMarketDataClient.get_quote()` 본문 구현. KIS 현재체결가 endpoint(`HHDFS00000300`, 모의 지원) 호출 → `Quote` 도메인 모델로 매핑. `PaperEngine.on_quote()`에 주입 가능해짐 → candidate scanner의 데이터 입력 확보.
4. **KIS_2** — `MISSING_OFFICIAL_VALUES.md` §2 계좌 + §4 주문 catalog 채우기 (자료 `uploads/6.xlsx`). docs only.
5. **api-account-001** — `KisAccountClient.get_account()` / `get_positions()` 본문 구현 (모의 지원 endpoint만).
6. **api-orders-paper-001** — `KisBroker.place_order()` 모의 주문 본문 구현. RiskEngine + OMS + KIS_ORDER_DRY_RUN 가드 유지.
7. **paper-002** — partial fill 다중 시퀀스 보강, 슬리피지 모델, market impact.
8. **strategy-002** — 새 전략(`PremarketGapVolumeBreakout` 외) 추가. Strategy Protocol 활용.
9. **runtime-002** — `PaperEngine.submit_intents()` 추가, dry-run controller와 paper-001 통합.
10. **roadmap 보강** — `docs/ai/MASTER_TRADING_ROADMAP.md`에 land된 작업 표시 + 다음 우선순위 명시.

---

## 9. 새 job 요청(`request.ko.md`) 작성 시 패턴

GPT가 만들 한국어 요청은 다음 골격을 따른다:

```markdown
# 작업 ID
{JOB_ID}              # 예: api-market-data-001, paper-001-gui, KIS_2

# 작업명
{한 줄 요약}

{1-3 문단 배경 + 동기}

## 목표

- 구체적 deliverable 1
- 구체적 deliverable 2
- ...

## 절대 하지 말 것

- KIS endpoint/TR ID/payload 추측 (위 §4 안전 규칙 상속)
- LLM의 broker 직접 호출 새 경로
- live trading 활성화
- 시장가 default-on
- `.env` 읽기/수정
- 실 API 키/계좌번호/토큰 코드/문서 노출
- 자동 git commit/push/merge/deploy
- (job별 추가 제한)

## 완료 기준

- 코드 변경 범위 명시
- 새 테스트 카운트
- `pytest` 회귀 0건
- 안전 grep 라벨 모두 clean
```

이걸 사람이 `docs/ai/jobs/{JOB_ID}/request.ko.md`에 저장 → Claude(나)에게 plan/codex-task 요청 → Codex로 구현.

---

## 10. 이전 job 사례에서 학습한 가이드라인

- **scope 분할 vs 통합**: 한 job 신규 LoC > 1000 이면 분할 권장. paper-001 (확장판)은 1100 LoC + 60 테스트로 한 pass에 들어가긴 했지만 review 부담 큼. 다음부터는 LoC ~500–700이 적절.
- **breaking 변경은 후방호환 우선**: paper-001에서 `PortfolioSnapshot`을 dict 시그니처로 바꾸려다 `app/api/routes.py`와 충돌. 해결: 단일 Decimal 필드 보존 + `_by_currency` 별 필드 추가.
- **시그니처 명확히**: codex-task에 함수 본문을 byte-level로 박는 게 Codex 일관성에 매우 효과적. 단 너무 길면 Codex가 일부 변형. 명령은 "본문 그대로 적용" + "이름 변경 금지" 명시.
- **plan deviation 잡기**: Codex는 plan에서 "더 안전한 대안 선택" 같은 미묘한 결정을 종종 놓침. plan에 강조 표시(예: `**MARKET intent에도 limit_price>0 요구**`) 권장.
- **multi-pass review 필요**: 1차 BLOCK/REQUEST CHANGES 후 fix → 2차 APPROVE 패턴 정상. 한 번에 끝나면 plan/codex-task가 부족했단 신호일 수 있음.
- **테스트 분할 vs 합본**: Codex가 종종 여러 test 파일을 하나로 합침(예: `test_paper_001_simulation_matrix.py`). 기능적 동등하면 OK, plan과 다른 파일명도 허용.

---

## 11. 본 브리핑을 GPT에게 줄 때 추가 컨텍스트로 묻는 질문 예시

GPT 프롬프트 마지막에 다음 형태로 묻기:

```
위 브리핑을 읽었으면, 다음 job용 한국어 요청(request.ko.md)을 작성해 줘:

작업 ID: {예: api-market-data-001}
목표 한 줄: {예: KIS 현재체결가 endpoint를 KisMarketDataClient.get_quote() 본문에 연결}
참고 자료: {예: docs/kis/MISSING_MARKET_DATA_VALUES.md의 §1.2 endpoint catalog, §2.1 Quote 응답 필드 매핑}

§9의 작성 패턴을 따르고, §4의 안전 규칙을 모두 상속하라. scope는 §10의 가이드라인대로 분할 검토하라.
```

GPT가 만든 request.ko.md를 사람이 `docs/ai/jobs/{JOB_ID}/request.ko.md`에 저장 → Claude(나)에게 전달 → plan/codex-task 작성 사이클 진입.

---

## 끝

본 브리핑은 2026-05-18 시점. paper-001 v2 APPROVE 직후. 다음 사이클은 사람의 commit 후 `paper-001-gui` 또는 `api-market-data-001` 우선 권장.

# Request Generator Brief — Paper Trading Project

본 문서는 GPT에게 **다음 job용 `request.ko.md`만 작성**시키기 위한 컨텍스트다. GPT는 코드/설계를 추론하지 않는다. 정해진 템플릿에 따라 새 job의 한국어 요청을 만든다.

---

## 1. 작성 대상

`docs/ai/jobs/{JOB_ID}/request.ko.md` 한 파일. 다음 사이클에서 Claude(planner)가 이걸 읽고 `plan.md`/`codex-task.md`를 만들고, Codex가 구현, Claude가 리뷰한다.

GPT는 **request.ko.md만** 출력. plan/codex-task/patch/review는 손대지 않는다.

---

## 2. request.ko.md 템플릿 (이 포맷 그대로 따르기)

```markdown
# 작업 ID
{JOB_ID}

# 작업명
{한 줄 요약 — 명사구}

{1–3 문단 배경 + 동기. 왜 지금 필요한지, 어떤 사용자 문제를 푸는지}

## 목표

- {구체적 deliverable 1}
- {구체적 deliverable 2}
- {…}

## 절대 하지 말 것

- {아래 §4 안전 규칙에서 본 job과 관련된 항목을 그대로 옮긴다}
- {job별 추가 제한이 있으면 추가}

## 완료 기준

- {예: 새 클라이언트 메서드 N개 본문 구현}
- {예: 새 테스트 N개 PASS, 기존 회귀 0건}
- {예: 안전 grep 라벨 모두 clean}
```

길이 가이드: 50~120줄. 너무 짧으면 plan에서 추측이 늘고, 너무 길면 의도가 흐려진다.

---

## 3. JOB_ID 명명 규칙

- 슬러그: 소문자 + 하이픈.
- 도메인 prefix:
  - `mvp-NNN` — 초기 스캐폴딩 (이미 mvp-001..mvp-023 사용됨, 새로 발급하지 말 것).
  - `paper-NNN` — 내부 paper trading 엔진 변경 (paper-001 land 완료).
  - `paper-NNN-gui` — 그 GUI 노출.
  - `api-{topic}-NNN` — KIS API 클라이언트 본문 구현 (api-auth-001 land 완료).
  - `strategy-NNN` — 새 전략.
  - `runtime-NNN` — 러너/오케스트레이션.
  - `KIS_N` — KIS docs/catalog 채우기 (KIS_1 land 완료).
  - `roadmap-*`, `docs-*` — 문서 전용.
- 본 시점 새 job 후보 명단은 §6 참고.

---

## 4. 안전 규칙 (모든 새 request.ko.md가 상속해야 하는 invariant)

GPT는 새 request.ko.md의 "절대 하지 말 것" 섹션에 본 job과 관련된 항목을 **반드시 옮긴다**. 새 invariant 만들기 금지.

1. paper trading이 기본. live trading 영구 비활성.
2. LLM/Agent는 executable order(`BrokerOrder`)를 절대 만들지 않는다. 추천 agent는 `OrderIntent`(non-executable)만 생성.
3. 모든 주문은 Strategy → RiskEngine → OMS → PaperBroker 통과.
4. `OrderType.MARKET`은 3중 가드(`ALLOW_PAPER_MARKET_ORDERS=true` AND `TradingMode.PAPER` AND `live_trading_enabled=False`) 통과 시만 RiskEngine 승인.
5. `ALLOW_MARKET_ORDERS=true`는 `load_settings()`가 즉시 reject. 절대 풀지 않는다.
6. 실 broker API 호출은 broker adapter 안에만. Strategy/agent/LLM이 broker 직접 호출 금지.
7. KIS endpoint/TR ID/payload/header **추측 금지**. 공식 자료(`docs/kis/MISSING_MARKET_DATA_VALUES.md`, `docs/kis/MISSING_OFFICIAL_VALUES.md`, `uploads/*.xlsx`)에서 확인된 값만 사용. 미확인 값은 `NotImplementedError`로 fail-closed.
8. 외부 HTTP 라이브러리(`requests`/`httpx`/`aiohttp`/`urllib3`) import 금지. stdlib `urllib.request`만 허용.
9. `.env` 읽기/수정 금지. `.env.example`은 변수 이름 + 한 줄 설명만 (값 0건).
10. 실 app key / app secret / access token / 계좌번호 / Bearer 토큰을 코드/문서/테스트/패치 어디에도 기록 금지. 테스트는 `"fake-*"` 또는 8자리 이하 fake 숫자만.
11. FX(환율) 변환 0건. multi-currency는 통화별 분리 보고만. `equity_total_in_base_currency`, `to_base_currency`, `exchange_rate` 같은 함수/상수 도입 금지.
12. `OrderType.STOP`(limit 없는 stop) 도입 금지. LIMIT/STOP_LIMIT/MARKET 3개만.
13. 자동 `git commit` / `git push` / PR merge / production 배포 금지.
14. GUI 파일(`app/api/`, `app/static/`, `app/main.py`)은 GUI 전용 job(`paper-NNN-gui` 등)에서만 수정. 그 외 job은 미접촉.

---

## 5. Scope 가이드라인

- 한 job 신규 LoC > 1000이면 **분할 권장**. paper-001 (확장판)이 ~1100 LoC + 60 테스트로 한 pass에 들어가긴 했지만 review 부담이 컸음. 다음부터는 LoC ~500–700이 적절.
- breaking 변경 시 후방호환 우선. 기존 API 시그니처 보존하면서 새 시그니처 추가 패턴.
- 한 job이 여러 도메인(예: 시세 + 주문 + 계좌)을 동시에 건드리면 분리. 단일 책임 원칙.
- 사용자 요청이 큰 묶음이면 GPT가 plan 단계 전에 분할안 1~2개 함께 제시.

---

## 6. 본 시점(2026-05-18) 다음 job 후보 (우선순위)

GPT는 사람이 어떤 후보를 골라 달라고 하면 그 후보의 request.ko.md를 만든다. 후보 본문은 GPT가 자유롭게 풀어 쓰되 안전 규칙(§4) + 템플릿(§2) 준수.

1. **paper-001-gui** — paper-001 데이터(`PaperAccount.cash`, `PaperJournal.trades`, 통화별 PnL)를 대시보드에 노출. GUI 전용 job.
2. **api-market-data-001** — `KisMarketDataClient.get_quote()` 본문 구현. KIS 현재체결가 endpoint 호출 → 도메인 `Quote` 모델로 매핑. `PaperEngine.on_quote()`에 주입 가능해짐. *KIS catalog 기반, endpoint 추측 금지.*
3. **KIS_2** — `docs/kis/MISSING_OFFICIAL_VALUES.md`의 §2 계좌 + §4 주문 catalog 채우기 (자료 `uploads/6.xlsx`). docs only.
4. **api-account-001** — `KisAccountClient` 본문 구현 (모의 지원 endpoint만, KIS_2 land 후).
5. **api-orders-paper-001** — `KisBroker.place_order()` 모의 주문 본문. RiskEngine + OMS + `KIS_ORDER_DRY_RUN` + KIS preflight 가드 유지.
6. **paper-002** — partial fill 다중 시퀀스 보강, 슬리피지 모델, market impact.
7. **strategy-002** — 새 전략 추가 (기존 `PremarketGapVolumeBreakout` 외).
8. **runtime-002** — `PaperEngine.submit_intents()` 추가 + dry-run controller와 paper-001 통합.
9. **roadmap 보강** — `docs/ai/MASTER_TRADING_ROADMAP.md` 갱신.

---

## 7. 좋은 request.ko.md 사례 (paper-001을 모범으로)

```markdown
# 작업 ID
paper-001

# 작업명
내부 paper trading MVP — fill 시뮬레이션 + cash + journal + 통합

GUI 작업은 중지하고, 백엔드 차원에서 "주문이 시작에서 fill까지 흘러가서 cash/positions/PnL이 실제로 갱신되는" end-to-end 흐름을 완성한다.

현재 Strategy→OMS→RiskEngine→PaperBroker 체인은 이미 wired되어 있지만, PaperBroker가 주문을 받기만 하고 fill을 만들지 않아 거래가 시작은 되되 끝나지 않는다. cash balance, Fill 모델, order/trade log, unrealized PnL이 빠져 있다.

## 목표

- `Fill` 도메인 모델 신설
- `PaperAccount`(cash ledger) + `PaperJournal`(order/trade log) + `PaperEngine`(quote→fill 처리) 신설
- `PaperBroker.tick(quote)` 구현: LIMIT/STOP_LIMIT/MARKET 매치, partial fill, staleness 검사, session 검사
- `PortfolioService`에 unrealized PnL + 통화별 PnL 노출 (단일 Decimal 필드는 후방호환)
- 통합 e2e 테스트로 BUY→SELL cycle이 닫히고 realized PnL이 정확함을 검증
- multi-currency 지원: `PaperAccount.cash`는 `dict[currency, Decimal]`. FX 변환은 하지 않음.

## 절대 하지 말 것

- live trading 활성화
- 실 broker API 호출
- `OrderType.MARKET` 도입 시 3중 가드(`ALLOW_PAPER_MARKET_ORDERS=true` + paper + !live) 우회
- `ALLOW_MARKET_ORDERS=true` 허용 (별 flag)
- FX 변환 함수 또는 환율 상수
- LLM/Agent의 broker 직접 호출 새 경로
- KIS/Alpaca broker 본문, dry-run 모듈, Strategy, OMS manager, GUI(`app/api/`, `app/static/`) 변경
- `.env` 읽기/수정
- 실 API 키/계좌번호/토큰을 코드/문서/테스트에 노출
- 자동 git commit/push/merge/deploy

## 완료 기준

- 새 모듈 (`Fill`/`PaperAccount`/`PaperJournal`/`PaperEngine`) 모두 단위 테스트 통과
- `PaperBroker.tick`이 LIMIT/STOP_LIMIT/MARKET × BUY/SELL 6가지 케이스 매치
- partial fill: `floor(quote.volume * PAPER_MAX_FILL_RATIO_OF_VOLUME)` cap, 잔량 누적
- staleness/session 검사 broker 내부
- multi-currency BUY/SELL cycle 통합 테스트 PASS
- 전체 pytest 회귀 0건, 안전 grep 6/6 clean
```

---

## 끝

GPT는 위 §2 템플릿 + §4 안전 규칙 + §5 scope 가이드라인 + §7 사례를 참고해서 사용자가 지정한 §6 후보 중 하나의 `request.ko.md`를 작성한다. 코드/플랜/패치는 만들지 않는다.

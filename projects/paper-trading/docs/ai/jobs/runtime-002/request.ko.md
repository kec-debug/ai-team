# 작업 ID
runtime-002

# 작업명
PaperEngine submit_intents 통합 — Quote → Strategy → RiskEngine → OMS → PaperBroker → Fill 흐름 연결

paper-001 v2에서 내부 paper trading 엔진이 구현되었고, `PaperBroker.tick(quote)`와 `PaperEngine.on_quote(quote)`를 통해 quote 주입 시 fill, cash, position, journal이 갱신되는 구조가 들어갔다.

하지만 현재 `PaperEngine.submit_intents()`가 없어 외부 caller가 직접 OMS를 호출한 뒤 별도로 `PaperEngine.on_quote(quote)`를 호출해야 하는 패턴이 남아 있다. 이 때문에 전략 후보가 실제 paper trading 엔진으로 들어가는 end-to-end 흐름이 명확하지 않고, dry-run controller와 paper engine 통합도 아직 끊겨 있다.

이번 작업의 목표는 `OrderIntent` 목록을 받아 Strategy → RiskEngine → OMS → PaperBroker 경계를 지키면서 paper order를 제출하고, 이후 quote가 들어왔을 때 `PaperEngine.on_quote()`가 fill/cash/position/journal을 갱신할 수 있도록 runtime 통합 계층을 만드는 것이다.

## 목표

- `PaperEngine.submit_intents()` 또는 동등한 runtime 진입점을 추가한다.
- 입력은 non-executable `OrderIntent` 목록만 허용한다.
- `OrderIntent`는 반드시 RiskEngine과 OMS를 통과해야 한다.
- OMS만 executable paper order를 생성할 수 있게 유지한다.
- PaperBroker는 OMS가 생성한 주문만 받게 한다.
- `PaperEngine.on_quote(quote)`와 `submit_intents()`가 같은 runtime 상태를 공유하도록 연결한다.
- dry-run controller가 직접 OMS를 우회하지 않고 `PaperEngine.submit_intents()`를 사용할 수 있게 한다.
- 제출 결과에는 accepted/rejected/blocked intent 수, order ids, rejection reasons를 포함한다.
- rejected/blocked intent는 PaperBroker로 넘어가지 않아야 한다.
- 기존 `PaperBroker.tick(quote)` / `PaperEngine.on_quote(quote)` / PaperAccount / PaperJournal 동작은 깨지지 않아야 한다.
- `KIS Quote` 또는 mock/synthetic Quote가 들어왔을 때 이후 fill 처리 흐름이 유지되어야 한다.
- runtime 단위 테스트와 end-to-end 테스트를 추가한다.
- Codex 작업 완료 후 `patch.md`에 Claude 검증 요청 프롬프트를 함께 작성하게 한다.
- Claude 리뷰 결과가 REQUEST CHANGES 또는 BLOCK일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙을 `patch.md`에 포함한다.

## 절대 하지 말 것

- live trading 활성화 금지.
- 실 broker API 호출 금지.
- KIS endpoint, TR ID, payload, header 추측 금지.
- KIS 주문, 계좌, 시세 HTTP 구현 금지.
- `Strategy`, `Agent`, `LLM`이 broker를 직접 호출하는 경로 추가 금지.
- LLM/Agent가 executable order(`BrokerOrder`)를 생성하게 만들지 말 것.
- 추천 agent는 `OrderIntent` 같은 non-executable intent까지만 허용.
- 모든 주문은 반드시 Strategy → RiskEngine → OMS → PaperBroker 경로를 통과해야 한다.
- OMS 우회 금지.
- RiskEngine 우회 금지.
- `ALLOW_MARKET_ORDERS=true` 허용 금지. `load_settings()`의 reject 정책을 풀지 않는다.
- `OrderType.MARKET` 3중 가드(`ALLOW_PAPER_MARKET_ORDERS=true` + `TradingMode.PAPER` + `live_trading_enabled=False`) 우회 금지.
- `OrderType.STOP` 도입 금지. LIMIT / STOP_LIMIT / MARKET 3개만 유지.
- FX 변환 함수, 환율 상수, base currency 변환 로직 도입 금지. 통화별 분리 보고만 허용.
- `.env` 읽기/수정 금지.
- `.env.example`에는 실제 값 추가 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호를 코드/문서/테스트/patch에 기록 금지.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3`) import 금지.
- GUI 파일(`app/api/`, `app/static/`, `app/main.py`) 수정 금지. 이 작업은 GUI 전용 job이 아니다.
- KIS 관련 파일을 실제 HTTP 구현 목적으로 수정하지 말 것.
- 자동 git commit / push / merge / production deploy 금지.

## 완료 기준

- `PaperEngine.submit_intents()` 또는 동등한 runtime entrypoint가 구현된다.
- `submit_intents()`는 non-executable `OrderIntent`만 입력으로 받는다.
- RiskEngine이 거절한 intent는 OMS와 PaperBroker로 넘어가지 않는다.
- OMS가 거절한 intent는 PaperBroker로 넘어가지 않는다.
- 승인된 intent만 OMS를 통해 paper order로 생성되고 PaperBroker에 등록된다.
- `PaperEngine.on_quote(quote)` 호출 시 기존처럼 `PaperBroker.tick(quote)` → `Fill` → `PaperAccount.apply_fill` → `PortfolioService.apply_trade` → `PaperJournal` 기록 흐름이 유지된다.
- dry-run controller가 직접 OMS/PaperBroker를 우회하지 않고 새 runtime entrypoint를 사용할 수 있다.
- LIMIT / STOP_LIMIT / MARKET의 기존 paper fill 테스트가 깨지지 않는다.
- MARKET은 기존 3중 가드 없이는 승인되지 않는다.
- partial fill, staleness, session check, cash ledger, realized/unrealized PnL 테스트가 계속 통과한다.
- Strategy 패키지에서 KIS 또는 broker 직접 import가 없어야 한다.
- Agent/LLM 경로에서 executable order 생성이나 broker 직접 호출이 없어야 한다.
- GUI 파일 변경이 없어야 한다.
- 전체 pytest 회귀 0건.
- 안전 grep이 clean이어야 한다.
- `patch.md`에 다음 항목이 포함되어야 한다.
  - 수정 파일 목록
  - `submit_intents()` 흐름 설명
  - RiskEngine/OMS/PaperBroker 경계 유지 확인
  - dry-run controller 통합 방식
  - live trading 비활성 유지 확인
  - market order guard 유지 확인
  - secret/account/token 노출 없음 확인
  - 테스트 결과
  - Claude 검증 요청 프롬프트
  - Claude 리뷰가 REQUEST CHANGES/BLOCK일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙
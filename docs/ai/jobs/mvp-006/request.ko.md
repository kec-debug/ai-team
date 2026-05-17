# 작업 ID
mvp-006

# 작업명
KIS 모의투자(한국투자증권) broker adapter 추가

> ⚠️ 이 초안은 mvp-005 후속으로 사용자 옵션 A 선택에 따라 Claude가 생성한 draft입니다.
> 검토 후 수정·확정해 주세요. 확정 시 plan.md / codex-task.md를 작성합니다.

`projects/paper-trading/`에 한국투자증권(KIS) 모의투자용 broker adapter를 추가한다.
현재 시스템은 미국주식 Alpaca Paper 기준으로 만들어져 있고, `.env`에 `KIS_PAPER_*` 키가 들어가 있지만 어떤 코드 경로도 읽지 않는다. 이번 작업은 그 갭을 메운다.

이번 목표는 실전매매가 아니라 paper(모의투자) 자동화다. live trading은 절대 활성화하지 않는다.
실제 KIS Open API HTTP 호출은 본 작업에서 구현하지 않는다(별도 후속 mvp). 이번에는 fail-closed stub + 설정 + 테스트까지.

## 포함

1. **`app/broker/kis_paper.py` 신규** — `BrokerAdapter` Protocol 구현, `mode = TradingMode.PAPER`.
   - `__init__(self, settings)`에서 `KIS_PAPER_API_BASE`(빈 값 또는 `https://`로 시작하지 않으면 `RuntimeError`), `KIS_PAPER_APP_KEY`/`KIS_PAPER_APP_SECRET`/`KIS_PAPER_ACCOUNT` 누락 시 `RuntimeError` (fail closed).
   - `submit`/`cancel`/`open_orders`/`positions` 모두 `NotImplementedError("KIS Paper network calls are not implemented in this phase")` stub.
   - URL은 코드에 하드코딩하지 않는다. 항상 `.env`에서 로드.

2. **`app/config.py` 확장** — `Settings`에 다음 필드 추가:
   - `kis_paper_api_base: str | None = None`
   - `kis_paper_app_key: str | None = None`
   - `kis_paper_app_secret: str | None = None`
   - `kis_paper_account: str | None = None`
   - `load_settings()`가 `.env`에서 위 4개를 읽어 `Settings`에 넣는다(누락은 `None`).
   - 파일 로드 단계에서는 KIS 키 검증을 강제하지 않는다(KIS를 안 쓰는 사용자가 깨지지 않도록). 검증은 `KisPaperBroker.__init__`에서만.

3. **(선택) `app/domain/enums.py`에 `Market` 열거형 또는 helper 추가** — 가장 적은 변경 선택.
   - 옵션 a) `Market(str, Enum)` 추가 (US, KR). 기존 `StrategyInput.market: str` 필드를 호환 유지(문자열 그대로 두되 KIS 어댑터는 KR 컨텍스트로 식별).
   - 옵션 b) 별도 `Market` enum 없이 문자열 `"KR"`만 지원. 가장 작은 변경.
   - 본 작업에서는 옵션 b)를 기본으로 한다(전략을 만들지 않으므로).

4. **KRX 시장 시간 helper(가벼움)** — `app/domain/krx_session.py` 또는 `app/utils/krx.py`로 `kst_session_for(ts: datetime) -> Session` 같은 함수만 추가. 본 작업의 어떤 코드도 이 함수를 호출할 의무는 없다(전략을 추가하지 않으므로). 미래 KRX 전략을 위한 hook이다. 시간 상수는 helper 안에만 둔다.
   - KRX 정규: 09:00–15:30 KST
   - 장전 동시호가: 08:30–09:00 KST → `Session.PRE_MARKET`로 매핑
   - 장후 시간외: 16:00–18:00 KST → `Session.AFTER_HOURS`로 매핑
   - 그 외 시간: `Session.CLOSED`
   - 함수만 추가, 어떤 모듈도 import할 필요는 없다.

5. **`app/api/routes.py` 일부 확장** — `/paper/status` 응답에 `brokers` 목록 추가:
   - 활성 broker(`PaperBroker`)와, 인스턴스화 가능한지 검증된 보조 broker(`AlpacaPaperBroker`, `KisPaperBroker`)를 메타정보로 노출.
   - 예: `"brokers": {"active": "PaperBroker", "configured": ["KisPaperBroker"]}` 형태.
   - `"configured"`는 env에 키가 있어 인스턴스화에 성공한 어댑터만 포함. credentials 노출 금지.

6. **테스트 추가 (`tests/test_kis_paper_stub.py` 신규)**:
   - `KisPaperBroker(settings)`에 빈 URL → `RuntimeError`.
   - `KisPaperBroker(settings)`에 `http://`(non-https) URL → `RuntimeError`.
   - `KisPaperBroker(settings)`에 credentials 누락 → `RuntimeError`.
   - 유효 placeholder 값을 채워 인스턴스화 후 `submit`/`cancel`/`open_orders`/`positions` 호출 → `NotImplementedError`.
   - `mode == TradingMode.PAPER`.

7. **회귀 테스트** — mvp-005의 기존 흐름이 깨지지 않음 확인:
   - `tests/test_flow.py`, `tests/test_paper_runner.py`, `tests/test_strategy_premarket_gap.py`, `tests/test_api_paper_status.py` 모두 그대로 통과해야 한다.
   - `/paper/status` 응답 변경이 기존 테스트와 호환되어야 한다(필요 시 기존 테스트 한두 줄만 보정).

## 제외 (이번 작업 아님)

- 실제 KIS Open API HTTP 호출 구현(별도 후속 mvp).
- KRX 한국 종목용 새 전략(premarket gap의 한국형 변형 등 — 별도 후속 mvp).
- 매매 전략 변경.
- 시장 데이터 연결.
- live trading 활성화.
- 실계좌(KIS 실전투자) 어댑터.
- mvp-005의 안전 불변식 변경.

## 금지

- 실계좌(KIS 실전투자) 어댑터 만들지 마.
- live trading을 true로 바꾸지 마.
- 시장가 주문 허용하지 마. `OrderType`에 MARKET 추가 금지.
- KIS endpoint URL 코드 하드코딩 금지. `.env`에서만 로드.
- API key/secret 코드 하드코딩 금지.
- `.env`(키 자체), secrets, auth, payment, production infra, database migrations 건드리지 마.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지.
- agent/LLM이 직접 주문하게 만들지 마.
- 임의 shell 명령 입력 기능 만들지 마.
- mvp-005 안전 불변식 유지: `OrderType`에 MARKET 없음 / Strategy가 OMS·Risk·Broker 미import / OMS의 `_risk`·`_broker` private / live 5단 차단.
- `/paper/status`나 어떤 응답에서도 credentials 노출 금지.

## 검증

- `python -m compileall app tests`
- `python -m pytest -p no:cacheprovider`
- `git diff --stat`
- `git status --short`

## 완료 후 정리

`patch.md`에:

1. 어떤 파일을 수정/추가했는지
2. `KIS_PAPER_*` 변수가 어떻게 `Settings`로 로드되는지
3. `KisPaperBroker`가 어떤 조건에서 fail closed로 차단되는지
4. live trading이 계속 차단되어 있는지(차단 5단이 그대로 유지되는지)
5. 시장가 주문이 여전히 생성될 수 없음(`OrderType`에 MARKET 없음 그대로) 확인
6. mvp-005 기존 테스트가 그대로 통과하는지
7. 다음 단계 (KIS HTTP 호출 실제 구현 / KRX 한국 시장 전략 / Alpaca HTTP 호출 실제 구현 중 어느 것을 먼저 할지)

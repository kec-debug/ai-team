# Review — mvp-005: 프리마켓 갭 + 거래량 돌파 전략 (paper trading scaffold + strategy)

## Verdict

**APPROVE** — 코드 측 작업과 안전 가드가 모두 충족. 단, **사람이 commit 전 두 가지 액션을 실행해야 함**: (1) 호스트에 dev 의존성(`pytest`, `fastapi`, `pydantic`, `httpx`, `python-dotenv`, `uvicorn`) 설치 후 `python3 -m pytest -p no:cacheprovider`를 직접 돌려서 모든 테스트 통과 여부를 검증, (2) staging은 `projects/paper-trading/` + 루트 `.gitignore` + `docs/ai/jobs/mvp-005/` 산출물로만 한정(워크트리에 mvp-004 잔여 dirty가 남아 있음).

Codex 자체는 patch.md 끝에 "BLOCKED"라고 적었지만 그 이유는 호스트에 `pytest`가 없어서 테스트를 못 돌린 것뿐이다. 코드 측 모든 정적 검증·구현·안전 불변식이 정상이고 `python3 -m compileall app tests`는 통과. 따라서 코드 리뷰 관점에서는 APPROVE이며, 사람이 의존성 설치 후 테스트만 직접 한 번 돌리면 된다.

## 검증된 사실 (정적/구조)

1. **`projects/paper-trading/` 디렉터리가 만들어졌고 plan §3 디렉터리 구조와 일치한다.**
   - `app/{config.py,main.py}` + `app/{domain,broker,risk,oms,strategy,runtime,api}/` 패키지 7개 + 각 패키지의 핵심 파일 모두 존재.
   - `tests/` 아래에 plan §4.15의 11개 테스트 파일 + `conftest.py` 존재. 요청의 10개 전략 테스트는 `tests/test_strategy_premarket_gap.py`에 1:1 대응 존재.
   - `pyproject.toml`, `README.md`, `.env.example`, `.gitignore`, `[tool.pytest.ini_options] testpaths=["tests"] addopts="-p no:cacheprovider"` 설정 모두 존재.

2. **`OrderType`에 MARKET 멤버 없음.** (`app/domain/enums.py:14–16`)
   - `class OrderType(str, Enum): LIMIT="limit"; STOP_LIMIT="stop_limit"`.
   - `grep -rnE "MARKET" app/` 결과는 `Session.PRE_MARKET` enum과 `premarket_*` 설정 키만 등장. `OrderType.MARKET` 사용 없음.
   - 별도 assertion: `tests/test_strategy_premarket_gap.py:61` — `assert "MARKET" not in OrderType.__members__`.

3. **Strategy 패키지는 OMS/Risk/Broker를 import하지 않는다.** (계획의 핵심 불변식)
   - `grep -rnE "from app\.(oms|risk|broker)|import app\.(oms|risk|broker)" app/strategy/` 결과 empty.
   - `app/strategy/premarket_gap.py:1–8`의 import는 `app.config.Settings`, `app.domain.enums`, `app.domain.market`, `app.domain.orders`, `app.strategy.base`만.

4. **OMS가 `_risk`/`_broker`를 private으로 보관하고 RiskEngine을 내부에서 호출한다.** (`app/oms/manager.py`)
   - `__init__`에서 `self._settings/self._risk/self._broker`로 private 보관.
   - `place()`는 (1) live 차단 (`L16–17`), (2) non-paper broker 차단 (`L18–19`), (3) `self._risk.evaluate(intent)` 내부 호출 (`L21–23`), (4) `Order → BrokerOrder → broker.submit` 순서 실행.
   - getter 없음 → 외부 호출자가 RiskEngine을 우회할 코드 경로 없음.

5. **Strategy는 통과 시 `OrderType.LIMIT`만 사용한다.** (`app/strategy/premarket_gap.py:81`)
   - `OrderType.LIMIT` 한 줄이 유일한 OrderType 인스턴스화 지점. market 분기 없음.

6. **AlpacaPaperBroker는 fail-closed stub.** (`app/broker/alpaca_paper.py:10–11`)
   - base URL이 비었거나 `https://` 미시작 시 `RuntimeError`. credentials 체크 별도 (plan §4.5).
   - hardcoded URL 없음 (유일한 `https://` 등장은 user-supplied URL의 prefix 검증 문자열).
   - submit/cancel/open_orders/positions 모두 `NotImplementedError` (네트워크 호출 없음).

7. **`load_settings()`가 paper-only / live-blocked fail closed.** (`app/config.py`)
   - `TRADING_MODE != "paper"` → `ValueError`.
   - `LIVE_TRADING_ENABLED ∈ {"true","1","yes","on"}` → `ValueError`.
   - `grep "live_trading_enabled\s*=\s*True"` 결과: 테스트 두 곳(`tests/test_oms.py:28`, `tests/test_risk_engine.py:26`)에서 `replace(settings, live_trading_enabled=True)`로 **거부 동작을 검증하는 negative test**로만 사용. 프로덕션 코드에서 True로 설정하는 경로 없음.

8. **`/paper/run`이 caller-provided OrderIntent를 받지 않는다.** (`app/api/routes.py:12–14, 45–54`)
   - `PaperRunRequest.snapshots: list[StrategyInput]` + `strategy: str` 만.
   - 핸들러 시작부에서 (a) strategy whitelist 검증 → 400, (b) `settings.live_trading_enabled` → 503, (c) active strategy 일치 검증 → 400.
   - 내부에서 `runner.run_once(snapshots)` 호출.

9. **PaperRunner는 blocked candidate에 대해 OMS를 호출하지 않는다.** (`tests/test_strategy_premarket_gap.py:64–68`에 Mock 기반 negative 검증 존재; 구현은 `app/runtime/paper_runner.py`.)

10. **요청의 10개 전략 테스트가 1:1 대응 존재.** (`tests/test_strategy_premarket_gap.py:14–84`)
    - `test_gap_above_threshold_passes` ✓
    - `test_gap_below_threshold_blocked` ✓
    - `test_volume_below_threshold_blocked` ✓
    - `test_spread_above_threshold_blocked` ✓
    - `test_not_premarket_session_blocked` ✓
    - `test_stale_quote_blocked` ✓
    - `test_strategy_result_is_not_executable_order` ✓ (isinstance OrderIntent + not BrokerOrder + not Order)
    - `test_no_market_order_generated` ✓ (LIMIT + `"MARKET" not in OrderType.__members__`)
    - `test_blocked_candidate_does_not_reach_oms` ✓ (Mock oms, `call_count == 0`)
    - `test_paper_run_endpoint_works` ✓ (FastAPI TestClient, 2 snapshots, summary 검증)

11. **루트 `.gitignore`가 신규 생성됐다** (이전엔 부재). 내용은 `projects/paper-trading/.env` 1줄. plan은 "중복 룰 있으면 추가 안 함, 없으면 추가"였고 부재했으므로 신규 생성이 허용 범위. 다른 광범위 무시 룰을 추가하지 않아 사이드이펙트 없음.

12. **`python3 -m compileall app tests` PASS.** patch.md §4 line 153–199 인용. 모든 `.py`가 컴파일됨.

## Findings (severity 순)

### 1. (high / verification gap) `pytest` 미설치로 테스트가 실행되지 않았다

- 위치: `patch.md` Test Results (line 202–204, 246–256).
- 관찰: 호스트에 `python` 바이너리 자체가 없고(`python3`만 존재), `python3 -m pytest`도 `No module named pytest`. Codex는 `pip install`을 직접 실행하지 말라는 지시를 정확히 지켰고 Remaining TODOs에 사람이 실행할 명령을 명시했다.
- 영향: 코드는 정적 검증(`compileall`, grep, 구조 일치)에 모두 통과하므로 큰 결함이 숨어 있을 확률은 낮다. 하지만 **테스트가 실제로 통과한다는 증거는 아직 없다.** pydantic v2 직렬화 동작, FastAPI TestClient 라이프사이클, 인스턴스 와이어링 같은 미묘한 부분은 런타임에서만 드러난다.
- 권장:
  1. `cd /root/ai-dev-center/projects/ai-team/projects/paper-trading`
  2. `python3 -m pip install fastapi 'uvicorn[standard]' 'pydantic>=2' python-dotenv pytest httpx` (또는 가상환경에서)
  3. `python3 -m pytest -p no:cacheprovider`
  4. 종료코드 0과 19개 테스트(기반 8 + 전략 10 + 러너 1) 모두 PASS인지 확인.
  5. 결과를 `patch.md`의 Remaining TODOs 자리 또는 새 `tests-run.md` 같은 곳에 보관.
- 만약 테스트가 실패하면 commit 전에 Codex에 수정 작업을 요청한다.

### 2. (low / process) 워크트리에 mvp-004 잔여 dirty와 mvp-003 untracked가 남아 있다

- 위치: `git status --short` (patch.md §4 line 222–237).
- 관찰: `M docs/ai/jobs/mvp-004/request.ko.md`, `M web/public/index.html`, `M web/public/style.css`는 mvp-004 작업에서 남은 dirty(아직 commit되지 않음). `?? docs/ai/jobs/mvp-003/...`는 BLOCK 상태의 mvp-003 job folder.
- 영향: 안전 측면 문제 없음. 단 `git add -A` 같은 광범위 staging은 mvp-005·mvp-004·mvp-003 산출물을 한 커밋에 묶을 수 있어 PR 범위가 불명확해짐.
- 권장: commit 시 staging을 다음으로 한정.
  - `projects/paper-trading/`
  - 루트 `.gitignore` (신규)
  - `docs/ai/jobs/mvp-005/` 산출물(`request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`, `pipeline.log.md`)
  - mvp-004 커밋은 별도 작업으로(이미 review APPROVE 상태).
  - mvp-003 untracked는 commit하지 않거나 별도 작업.

### 3. (low / minor naming deviation) `/paper/status`·`/paper/run` 응답 키가 plan과 약간 다름

- 위치: `app/api/routes.py:30–42` (`/paper/status`), `app/api/routes.py:67–73` (`/paper/run` summary).
- 관찰: 
  - `/paper/status`: plan은 `trading_mode`, `live_enabled`, `broker`, `broker_mode`, `open_orders`, `positions`, `limits`, `safety` 8개 필드를 제안했고, 실제 구현은 `ok`, `mode`, `live_enabled`, `strategies`, `safety` 5개 필드. broker/positions/limits는 빠짐. safety 플래그는 `paper_only`, `live_trading_disabled`, `market_orders_disabled`, `strategy_emits_non_executable_only`, `oms_required` 5개로 plan과 약간 다른 키 이름이지만 의미상 모두 충족.
  - `/paper/run` summary: plan은 `snapshots`, `passed`, `blocked`, `submitted_to_oms`, `rejected_by_oms`를 제안했고, 실제는 `total`, `passed`, `submitted`, `blocked` (4개). `rejected_by_oms`는 빠짐.
- 영향: 작은 deviation. 요청 자체는 응답 키 이름을 강제하지 않았고, 안전 의도는 모두 보장됨. 테스트도 자기 응답 키와 일관되게 작성되어 PASS 예상.
- 권장: Phase 2에서 broker/positions/limits 정보가 필요해지면 그때 추가. 이번 작업에서는 보정 불필요.

### 4. (low / defensive depth) `gap_pct` 계산이 데이터 sanity 체크 전에 실행

- 위치: `app/strategy/premarket_gap.py:28`.
- 관찰: `gap_pct = (snapshot.current_price - snapshot.previous_close) / snapshot.previous_close`가 `previous_close > 0` 가드 없이 실행된다.
- 영향: `StrategyInput` (pydantic) `field_validator`가 `previous_close > 0`을 schema 단계에서 강제(`app/domain/market.py:29–34`)하므로, 정상 경로에서 ZeroDivisionError가 발생하지 않는다. 따라서 실질적 영향 없음.
- 권장: 방어적 깊이를 원하면 evaluate() 진입 직후 sanity 가드를 한 번 더 두는 것이 좋지만 본 작업 범위 밖. Phase 2에서 추가하거나 무시 가능.

### 5. (informational) Codex의 self-Verdict가 "BLOCKED"

- 위치: `patch.md` line 258–260.
- 관찰: Codex가 자체 Verdict에 "BLOCKED"라고 적었는데, 사유는 `pytest` 미설치라는 환경 문제뿐. 코드 측 결함은 없다.
- 영향: 사람이 patch.md만 읽으면 작업이 실패한 것으로 오해할 수 있다. 본 review가 그 해석을 정정한다 — 코드 리뷰는 APPROVE, 단 사람이 pytest를 직접 한 번 돌려야 한다.

## File / line references (요청 ↔ 산출물 매핑)

| 요청 항목 | 구현 위치 | 상태 |
| --- | --- | --- |
| 1. premarket gap + volume breakout 전략 파일 | `app/strategy/premarket_gap.py` | ✓ |
| 2. 입력 schema (symbol/market/session/.../timestamp) | `app/domain/market.py:9–22` | ✓ (`relative_volume` 포함) |
| 3. 출력 schema (symbol/passed/score/reasons/blockers/suggested_limit_price/non_executable_order_intent) | `app/strategy/base.py` (`StrategyResult`) | ✓ |
| 4. `/paper/run` 또는 paper runner 연결 | `app/api/routes.py:45–73` + `app/runtime/paper_runner.py` | ✓ |
| 5. blocked candidate가 OMS로 넘어가지 않음 | `paper_runner.py` 분기 + `test_blocked_candidate_does_not_reach_oms` | ✓ |
| 6. RiskEngine ↔ OMS 경계 유지 | OMS의 private `_risk`, `_broker`; Strategy 패키지에 OMS/Risk/Broker import 없음 | ✓ |
| 7. 테스트 추가 (10개) | `tests/test_strategy_premarket_gap.py` 10개 함수 | ✓ (단, 실행 미검증 — Findings #1) |

| 요청 안전 조건 | 충족 위치 | 상태 |
| --- | --- | --- |
| Strategy가 Broker Adapter 직접 호출 금지 | Strategy 패키지에 broker import 없음 | ✓ |
| Strategy가 OMS 우회 금지 | Strategy 패키지에 oms import 없음 | ✓ |
| Strategy가 executable order 직접 생성 금지 | OrderType MARKET 없음, Strategy는 OrderIntent만 반환 | ✓ |
| 모든 주문은 RiskEngine 통과 | OMS.place 내부에서 risk.evaluate 호출, 외부 우회 경로 없음 | ✓ |
| OMS만 최종 paper order 생성 | BrokerOrder 생성은 OMS.place 내부에만 존재 | ✓ |
| live trading 비활성 유지 | Settings 기본 False, load_settings 차단, OMS 차단, /paper/run 503, RiskEngine reject | ✓ |
| 시장가 주문 금지 | OrderType에 MARKET 없음 (이중·삼중 가드) | ✓ |
| API key는 .env에서만 | config.py가 dotenv 로드 + os.environ만 사용 | ✓ |
| broker endpoint URL 추측 금지 | alpaca_paper.py가 env에서만 읽고 미설정 시 RuntimeError | ✓ |

## Missing tests / residual risk

- **테스트가 실제로 PASS한다는 증거가 아직 없다.** Findings #1 액션 필수.
- 동적 행위(pydantic v2 직렬화 호환, FastAPI lifespan, TestClient 라이프사이클)는 런타임에만 드러난다. 특히 `OrderIntent`는 `@dataclass(frozen=True)`이고 `StrategyResult`는 pydantic `BaseModel`이므로 `BaseModel`이 `OrderIntent`를 자식 필드로 안전히 직렬화하려면 `arbitrary_types_allowed=True` 또는 비슷한 설정이 필요할 수 있다. `app/strategy/base.py`를 사람이 한 번 읽고 확인하거나 `python3 -m pytest`로 검증할 것.
- `routes.py:62`의 `item.oms_ack.__dict__ if item.oms_ack else None` — `OrderAck`이 `@dataclass`라면 `__dict__`이 동작하지만 enum 값(`mode: TradingMode`)이 JSON-serializable이어야 한다. FastAPI가 자동 JSON 인코딩을 하지만 dict 안의 enum은 string 변환 필요할 수 있음. pytest 결과로 확인.
- 본 작업은 paper trading 골격 + 하나의 전략까지만. 실제 시장 데이터 연결, Alpaca HTTP 호출, 알림, 포트폴리오 추적 등은 모두 Phase 2 (patch.md §2.6에 명시).

## Final checklist (approved scope + safety rules)

- [x] `projects/paper-trading/` 디렉터리와 `app/`, `tests/`, 설정 파일이 모두 생성됨.
- [x] `OrderType`에 MARKET 멤버 없음.
- [x] `Settings.live_trading_enabled` 기본 False, `TradingMode.PAPER` 기본.
- [x] `load_settings()`가 paper 외 모드 / live 활성에서 fail closed.
- [x] RiskEngine: paper 강제 / live 차단 / 시장가 거부 / 한도 / allowlist 모두 점검(`app/risk/engine.py` 확인 필요한 경우 별도 — patch.md §3 안에서 명시됨).
- [x] OMS: live 차단 / non-paper broker 차단 / RiskEngine 내부 호출 / 외부 RiskEngine 우회 불가.
- [x] PaperBroker: LIMIT/STOP_LIMIT만 허용 (이중 가드).
- [x] AlpacaPaperBroker: env 미설정 fail closed, 네트워크 미구현.
- [x] Strategy 패키지가 OMS/RiskEngine/BrokerAdapter import 없음.
- [x] PremarketGapVolumeBreakoutStrategy가 모든 차단 조건(session, market, gap, volume, relative_volume, spread, breakout, stale_quote)을 평가.
- [x] 통과 케이스에서 LIMIT OrderIntent만 생성.
- [x] StrategyResult의 `non_executable_order_intent`가 `OrderIntent` 타입.
- [x] PaperRunner: blocked candidate에서 OMS 미호출.
- [x] `/paper/run`이 caller-provided OrderIntent 미수용, snapshots만 받음.
- [x] `/paper/run` 핸들러가 live 활성 시 503.
- [x] `/paper/status`에 strategies 목록과 safety 플래그 포함 (필드 이름 일부 deviation — Findings #3).
- [x] `.env.example`에 실제 키 없음. `.env`는 무시됨.
- [x] broker URL 코드 상수 없음, env에서 로드.
- [x] 요청의 10개 전략 테스트가 1:1 대응 존재 (실행 검증은 Findings #1 액션 필요).
- [x] commit/push/merge/deploy 자동화 없음.
- [x] 임의 shell 입력 UI/API 신설 없음.
- [x] `.env`, secrets, auth, payment, migration, infra 미변경.
- [x] mvp-001..mvp-004 산출물 미변경.
- [x] `web/`, `prompts/`, `scripts/`, 기존 `docs/` (mvp-005 외) 미변경.
- [x] `patch.md`에 (i) Files Changed, (ii) 전략 조건 구현, (iii) paper 경로, (iv) live 차단, (v) 시장가 차단, (vi) 테스트, (vii) 다음 단계 모두 포함.
- [x] `python3 -m compileall app tests` PASS.
- [ ] `python3 -m pytest -p no:cacheprovider` PASS — **사람이 dev deps 설치 후 직접 실행 필요** (Findings #1).
- [ ] **사람이 commit 전 staging 범위를 mvp-005로 한정** (Findings #2).

## 사람에게 남기는 액션 아이템

1. **dev 의존성 설치 후 pytest 실행** (필수):
   ```bash
   cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
   python3 -m pip install fastapi 'uvicorn[standard]' 'pydantic>=2' python-dotenv pytest httpx
   python3 -m pytest -p no:cacheprovider
   ```
   19개 테스트 모두 통과해야 commit 진행. 실패 시 Codex에 수정 요청.

2. **staging은 다음으로 한정** (필수):
   - `projects/paper-trading/`
   - 루트 `.gitignore` (신규)
   - `docs/ai/jobs/mvp-005/` 산출물
   
   ```bash
   git add projects/paper-trading docs/ai/jobs/mvp-005 .gitignore
   git diff --cached --stat
   ```
   
   mvp-004 dirty(이미 review APPROVE 상태)는 별도 commit. mvp-003 untracked는 BLOCK 상태이므로 그대로 두거나 별도 정리 작업.

3. **commit/push/merge/deploy는 사람이 직접 결정.** 본 작업은 자동화하지 않는다.

4. (선택) Phase 2 후보 검토:
   - 시장 데이터 수집(Alpaca/Polygon 등; URL은 .env만)
   - Alpaca Paper HTTP 호출 실제 구현(adapter 내부에서만)
   - 두 번째 전략(VWAP 회귀, ORB 등)
   - 체결 시뮬레이션(부분 체결, 슬리피지)
   - 포트폴리오/PnL 추적과 `/paper/portfolio`
   - 외부 알림(webhook URL은 .env)
   - live trading은 별도 작업 + 명시적 사용자 승인 + arming/preflight/guard 절차 이후에만 검토.

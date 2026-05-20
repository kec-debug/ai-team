# agent-platform-spec-001 — Agent 플랫폼 최종 설계 (85 역할 모듈 + 7 실행 서비스 + Top 15+5) plan

본 plan 은 **design-documentation only**. 다음 turn 에서 Codex 가 11 개 한국어 design 문서 + patch.md 를 생성한다. application code / tests / `.env` / KIS catalog / runtime 일체 무변동.

## 1. 요청 요약

`final-platform-plan/04_agent_strategy_pipeline.md` 는 7 종 agent 의 초기 design 만 정의했다. 본 작업은 그 위에:

- **최종 설계 — 85 역할 모듈** (실시간 핵심 40 / 보조 뉴스·이벤트 10 / 검증·학습 20 / 운영·보안 15) 의 한국어 design.
- **7 실행 서비스** (Orchestrator / Market Data / Strategy / Broker Gateway / News & Event / Validation & Learning / Ops & Security) 의 process boundary + 통신 + kill switch propagation + 85 모듈 → 7 서비스 매핑.
- **실제 시작점 Top 15 critical + 5 Claude/Codex meta-agent** 의 우선순위 + 의존 그래프.
- 각 모듈의 typed I/O / score / confidence / reasons / blockers / metadata / provider / fallback / parse_status.
- LLM provider abstraction (optional + deterministic fallback + Pydantic validation).
- `final-platform-plan/09_implementation_backlog.md` 의 agent 영역을 정밀화하는 sub-backlog (85 + 7 + 5 = 97 item).

본 design 의 핵심 invariant — `final-platform-plan` 의 안전 원칙 + 7 서비스 분리 + Broker Gateway 격리:

- Agent (역할 모듈) 는 broker 를 직접 호출하지 않는다.
- OMS 만 executable `BrokerOrder` 생성. OMS 는 Strategy Service 안.
- **Broker Gateway Service 만 KIS 자격증명 보유 + KIS API 호출.**
- 주문 경계: `Strategy(Strategy Svc) → RiskEngine(Strategy Svc) → OMS(Strategy Svc) → BrokerAdapter(Broker Gateway Svc)`.
- "거래 에이전트" (Top 15 #10) 는 Strategy Service 의 IntentEmitter role. broker 호출 0.
- "비상정지 에이전트" 는 Orchestrator Service 가 kill switch broadcast.
- LLM optional + deterministic fallback. LLM 단독 hard risk block 해제 불가.
- 실 KIS endpoint / TR_ID / payload 추측 0.
- live trading 활성화 코드 0.
- 서비스 간 통신은 loopback / 내부망 한정. 외부 endpoint 추가 0.

## 2. 작업 범위

### 2.1 포함 (본 turn 의 Claude 가 작성)

- `request.ko.md` (이미 작성, 85+7 구조 반영).
- `plan.md` (본 파일).
- `codex-task.md`.

### 2.2 Codex 가 다음 turn 에 생성 (11 design docs + patch.md, 한국어)

- `00_principles_and_boundaries.md` — 안전 원칙 + Agent ≠ Broker + 85 모듈 / 7 서비스 경계.
- `01_seven_services.md` — 7 실행 서비스 design + process boundary + 통신 프로토콜 + kill switch broadcast + 85 → 7 매핑 표.
- `02_realtime_core_40_agents.md` — 실시간 핵심 40 에이전트.
- `03_news_event_10_agents.md` — 보조 뉴스/이벤트 10 에이전트.
- `04_validation_learning_20_agents.md` — 검증/학습 20 에이전트.
- `05_ops_security_15_agents.md` — 운영/보안 15 에이전트.
- `06_top15_focus_set.md` — Top 15 critical + 5 meta-agent (의존 그래프, 진입 순서, P0/P1/P2).
- `07_llm_provider_design.md` — LLM provider Protocol + 기본 deterministic + Pydantic validation + fallback chain.
- `08_data_contracts.md` — `AgentInput` / `AgentOutput` / `AgentTrace` / `KillSwitchCommand` / `AlertEvent` / `ServiceMessage` typed contracts.
- `09_implementation_backlog.md` — 85 모듈 + 7 서비스 + 5 cross-cutting = 97 backlog item (Job ID / Phase / Size S·M·L / 의존 / acceptance / test plan / risk / rollback).
- `10_acceptance_criteria.md` — 본 design + 후속 implementation job 공통 acceptance template.

### 2.3 절대 제외

- `app/` / `tests/` / `scripts/` / `docs/kis/` / `.env` / `.env.example` / `README.md` / `docs/RUNBOOK.md` / `docs/OPS_AUDIT.md` 어떤 파일도 modify/create/delete.
- 다른 job 디렉터리 (`final-platform-plan/` 포함) 수정 — read-only 인용만 OK.
- 새 endpoint / 새 KIS endpoint / 새 TR ID / 새 payload / 새 response field 추측.
- 외부 web fetch.
- live trading 활성화 / live arm / `KIS_ORDER_DRY_RUN=false` 토글.
- 자동 git commit / push / merge / deploy.
- 수익 보장 / 거짓 성과 / 과장된 승률 / 시간 추정.
- 본 turn 또는 다음 turn 에서 application code 작성.
- 7 서비스를 외부에 공개하는 endpoint 추가 권고.
- Broker Gateway 외 다른 서비스가 KIS 자격증명을 보유하는 design.

## 3. 7 실행 서비스 design 기반 (Codex 가 `01_seven_services.md` 에서 완성)

### 3.1 7 서비스 책임 (권고, Codex 가 확장 / 보정 가능)

| # | 서비스 | 책임 | 내부 역할 모듈 (예시) | KIS 자격증명 | broker 호출 |
| --- | --- | --- | --- | --- | --- |
| 1 | Orchestrator Service | 모든 서비스의 lifecycle + 스케줄링 + kill switch broadcast + 운영자 명령 | 오케스트레이터, 세션 관리, 모니터링 일부 | 0 | 0 |
| 2 | Market Data Service | 시세 / 호가 / 스냅샷 / 외부 데이터 read-only 수집 + 정규화 + 캐시 | 데이터, 스캐너, 일부 실시간 핵심 | 0 (시세 전용 채널만, paper 모드 default) | 0 |
| 3 | Strategy Service | 분석 / 전략 / 리스크 / 사이징 / IntentEmitter. `Strategy → RiskEngine → OMS` 격리 보존 | 실시간 핵심 다수 (분석, 전략, 리스크, 포지션 사이징, 거래 IntentEmitter, 주문 감시) | 0 | 0 (BrokerOrder 를 Broker Gateway 로 RPC) |
| 4 | Broker Gateway Service | 유일하게 KIS 자격증명 보유. OMS 의 검증된 `BrokerOrder` 만 받아 KIS API 호출. paper TR_ID 만, `KIS_ORDER_DRY_RUN` 게이트. | 거래 게이트웨이, 주문 감사 일부 | **유일** | **유일** |
| 5 | News & Event Service | 뉴스 / 공시 / 이벤트 수집 + 분류 + 신뢰도 평가. Strategy Service 에 알림 emit. | 뉴스/이벤트 10 모듈 | 0 | 0 |
| 6 | Validation & Learning Service | 백테스트 / 슬리피지·스프레드 검증 / 일일 리포트 / 학습 / 전략 비교. 모두 read-only. | 검증/학습 20 모듈 | 0 | 0 |
| 7 | Ops & Security Service | 모니터링 / 비상정지 / 보안 / 시크릿 / 실계좌 잠금 / 주문 감사 / 장애 복구 / 실전 전환 승인 (locked) | 운영/보안 15 모듈 | 0 (단, 시크릿 매니저 모듈이 자격증명 발급/회수만 — Broker Gateway 가 사용) | 0 |

### 3.2 통신 프로토콜 (권고)

- 모든 서비스 간 통신: **loopback HTTP** (127.0.0.1) 또는 **UNIX domain socket**. 외부 노출 0.
- Auth: 내부 토큰 (rotated by 시크릿 매니저). 외부 공개 0.
- Strategy Service → Broker Gateway Service: 유일 write 채널. `BrokerOrder` payload 만 허용. `OrderIntent` 직접 전달 0 (RiskEngine 통과 후 OMS 가 변환한 검증된 `BrokerOrder` 만).
- Orchestrator → all services: kill switch broadcast. 모든 서비스가 즉시 새 action 중단.
- Market Data → Strategy / News / Validation: read-only `Quote` / `Snapshot` push 또는 pull.
- News → Strategy: read-only event push.
- Validation → Ops: read-only metrics push.
- API/UI 는 별 layer (기존 FastAPI) — `/ops/*` / `/paper/*` 기존 endpoint 만 노출. 신규 endpoint 0.

### 3.3 Kill switch propagation

- Orchestrator Service 가 kill switch engaged 시 모든 서비스에 broadcast.
- Strategy Service: 새 OrderIntent 생성 중단.
- Broker Gateway Service: 새 BrokerOrder 수신 거부 (cancel 만 허용 — 단, 자동 cancel 도 운영자 명시 승인 후만).
- News / Validation / Market Data: 데이터 수집은 지속, action 0.
- Ops & Security: 감사 로그 계속.
- Kill switch 해제는 운영자 수동 (RUNBOOK 절차). 자동 해제 0.

### 3.4 85 모듈 → 7 서비스 매핑

Codex 가 `01_seven_services.md` 안에 다음 형식의 매핑 표 생성:

| 카테고리 | 모듈 # | 역할 모듈 명 (한국어) | 영어 alias | 소속 서비스 |
| --- | --- | --- | --- | --- |
| 실시간 핵심 | 1 | 오케스트레이터 에이전트 | `OrchestratorAgent` | Orchestrator |
| 실시간 핵심 | 2 | 세션 관리 에이전트 | `SessionManagerAgent` | Orchestrator |
| 실시간 핵심 | 3 | 데이터 에이전트 | `DataAgent` | Market Data |
| ... | ... | ... | ... | ... |

85 행 모두. Codex 가 각 모듈을 정확히 한 서비스에 배치.

## 4. 각 design 문서 — 필수 포함 항목

각 문서는 한국어 + 운영자 readable + 개발자 backlog 변환 가능 + plan §3 의 안전 invariant 반복.

### 4.1 `00_principles_and_boundaries.md`

- §3 (7 service) + 안전 invariant 전체.
- Agent / Strategy / RiskEngine / OMS / BrokerAdapter / KisBroker / PaperBroker 의 관계 ASCII 도식 + 7 서비스 boundary 표시.
- 역할 모듈 (Agent) 의 input source / output sink.
- Broker Gateway 격리 명시 — KIS 자격증명은 1 서비스에만.
- "거래 에이전트" broker 호출 0 / "비상정지 에이전트" 유일 mutation.
- 위반 시 review BLOCK 사유.

### 4.2 `01_seven_services.md`

- 7 서비스 각각의 책임 / 소속 모듈 / KIS 자격증명 유무 / broker 호출 유무 / 통신 패턴.
- ASCII 아키텍처 도식 (서비스 박스 + RPC 화살표 + KIS 외부 박스).
- 서비스 간 통신 프로토콜 (loopback HTTP / UNIX socket / 내부 토큰).
- Kill switch broadcast 흐름.
- 장애 / 재시작 시나리오 (서비스 A 죽으면 B 가 어떻게 동작 — fail-closed 원칙).
- 85 모듈 → 7 서비스 매핑 표 (전체 85 행).
- 향후 deployment topology (docker-compose / systemd unit / supervisor 등은 implementation job 으로 위임, design 에서는 boundary 만).

### 4.3 `02_realtime_core_40_agents.md`

40 모듈 (실시간 핵심) 각각:

| 항목 | 내용 |
| --- | --- |
| # / 한국어 명칭 / 영어 alias | |
| 소속 서비스 | |
| 책임 (한 줄) | |
| Input (typed) | 필드 / 타입 / source |
| Output (typed) | 필드 / 타입 / 다음 모듈 |
| Score / Confidence | |
| Reasons / Blockers | 예시 |
| Provider | rule-based / LLM optional |
| Fallback | deterministic |
| Parse status | ok / malformed / timeout |
| 안전 가드 | read-only / kill switch / dry-run |
| 의존 모듈 | |
| 다음 모듈 | |

40 모듈 권고 (Codex 가 보정 가능, 같은 책임을 중복 정의하지 않을 것):

오케스트레이터, 세션 관리, 데이터 수집, 데이터 정규화, 데이터 캐시, 데이터 무결성, 스캐너, 종목 universe 관리, 종목 metadata, 호가 모니터, 거래량 모니터, 변동성 모니터, VWAP/세션 통계, ORB (Opening Range Breakout) 분석, 추세 분석, 모멘텀 분석, 변동성 분석, 평균회귀 분석, 거시지표 분석, 산업/섹터 분석, 전략 선택, 신호 종합, 리스크 (사전), 리스크 (실시간), 포지션 사이징, 한도 관리, 진입 가격 산정, 손절가 산정, 익절가 산정, 거래 에이전트 (IntentEmitter), 주문 검증, 주문 감시, 부분 체결 처리, 미체결 관리, 슬리피지 감시, 가격 추적, 포트폴리오 모니터, P&L 실시간, 리스크 이벤트 모니터, 모듈 헬스 (총 40).

특히:

- **거래 에이전트** — alias `IntentEmitterAgent`. broker 호출 0. `OrderIntent` 생성 → OMS 위임. Strategy Service 안.
- **리스크 모듈** 들 — `RiskEngine` 의 input feed 가 되거나 보조. 최종 RiskVerdict 는 RiskEngine 만.

### 4.4 `03_news_event_10_agents.md`

10 모듈 (뉴스/이벤트). 모두 read-only. 주문 0.

권고 (Codex 가 보정 가능):

뉴스 수집, 뉴스 분류, 뉴스 신뢰도 평가, 공시 모니터, 실적 발표 모니터, 거시 이벤트, 정정/구속력 이벤트, 가격 충격 추정, 뉴스 → 종목 매핑, 이벤트 알림 emit (총 10).

### 4.5 `04_validation_learning_20_agents.md`

20 모듈 (검증/학습). 모두 read-only. 주문 0.

권고 (Codex 가 보정 가능):

검증, 백테스트, 슬리피지 검증, 스프레드 검증, 체결 현실성 검증, 매매일지 분석, 일일 리포트, 주간 리포트, 전략 비교, 전략 성과 분해, 실패 원인 분류, 회귀 비교, 데이터 품질 검증, 신호 노이즈 분석, LLM 결과 검증 보조, 학습 (paper 결과 → 파라미터 조정 제안만, 자동 적용 0), 파라미터 튜닝 추천, 결정 트리 추출, 가설 검증, 결과 시각화 (총 20).

### 4.6 `05_ops_security_15_agents.md`

15 모듈 (운영/보안).

권고 (Codex 가 보정 가능):

모니터링, 비상정지, 보안 (시크릿 leak grep), 시크릿 관리, 실계좌 잠금, 규정 체크, 세금 기록, 계좌 보호, 주문 감사, 장애 복구, 실전 전환 승인 (locked), 로그 회전/보관, 알림 라우팅 (Slack 등), 운영자 명령 처리, 운영자 권한 관리 (총 15).

특히:

- **비상정지** — kill switch set 유일 mutation. Orchestrator broadcast.
- **실계좌 잠금** — `live_trading_enabled=False` 강제.
- **실전 전환 승인** — locked / future-approval-gated.
- **시크릿 관리** — Broker Gateway Service 만 자격증명 수신. 다른 서비스 차단.

### 4.7 `06_top15_focus_set.md`

Top 15 critical + 5 meta-agent.

각 모듈에:

- 영어 alias.
- 소속 서비스.
- 위 02~05 doc 의 참조 (어느 카테고리에 속하는지).
- 우선순위 (P0 / P1 / P2).
- 의존 모듈 (어떤 모듈이 먼저 land 되어야 하는가).
- 진입 순서 ASCII DAG.
- backlog item ID (`09_implementation_backlog.md` 의 ID 와 1:1).

권고 P0 진입 순서:

1. 오케스트레이터 (모든 lifecycle).
2. 세션 관리.
3. 데이터 에이전트.
4. 비상정지 (안전망 우선 land).
5. 주문 감시 (기존 `/paper/orders`, `/paper/fills` 재사용).
6. 거래 로그.
7. 스캐너 / 뉴스/이벤트.
8. 분석 / 전략 선택 / 리스크 / 포지션 사이징.
9. 거래 에이전트 (IntentEmitter).
10. 검증.
11. 학습/리포트.

권고 5 meta-agent P0 (위험도 낮은 순):

LLM 결과 검증 → Codex 테스트 → Claude 리뷰 → Claude 설계 → Codex 구현.

### 4.8 `07_llm_provider_design.md`

- `LLMProvider` Protocol (pseudocode, 실 `.py` 작성 0).
- Default: `DeterministicProvider` (rule-based).
- Optional: `OpenAIProvider` / `AnthropicProvider` / etc. 추상 정의만.
- Fallback chain: LLM A → LLM B (옵션) → deterministic.
- Pydantic validation 강제. malformed → 재시도 1 회 → deterministic fallback.
- Retry / timeout / cost-rate awareness.
- 시크릿 격리 — agent 코드 raw secret 0. 시크릿 매니저 (Ops Service) 중개.
- LLM 출력은 hard risk block 풀 수 없음.
- `AgentTrace.provider_used` / `fallback_used` / `parse_status` 기록.

### 4.9 `08_data_contracts.md`

Typed contracts 표:

- `AgentInput` (base).
- `AgentOutput` (score / confidence / reasons / blockers / metadata / trace).
- `AgentTrace` (provider_used / fallback_used / parse_status / duration / cost).
- `AgentLifecycleState` (idle / running / paused / error / stopped).
- `KillSwitchCommand`.
- `AlertEvent`.
- `ServiceMessage` (7 서비스 간 RPC payload base).
- `OrderIntent` (기존 인용, 재정의 0).
- `BrokerOrder` (기존 인용, Broker Gateway 수신 payload).

각 contract 의 필수/옵션 필드 + 기본값 + source + sink.

### 4.10 `09_implementation_backlog.md`

표 형식. 97 backlog item:

- 85 모듈 (각 모듈 1 row).
- 7 서비스 (각 서비스 1 row — 서비스 골격 / 통신 / health check).
- 5 cross-cutting:
  - `agents-base-001` — `AgentBase` abstract + contracts.
  - `agents-llm-provider-001` — `LLMProvider` Protocol + deterministic.
  - `services-rpc-base-001` — 서비스 간 RPC base + auth.
  - `kill-switch-broadcast-001` — Orchestrator → 6 서비스 broadcast.
  - `agents-test-base-001` — agent / service 회귀 인프라.

| Job ID | Phase / 카테고리 | 소속 서비스 | Size | Purpose | 수정 파일 | 신규 파일 | 의존 backlog | Acceptance | Test plan | Risk | Rollback |

시간 추정 0. Size 는 S/M/L.

마지막 섹션: prioritization logic (Top 15 + 5 = P0, 그 외 P1/P2 분배).

### 4.11 `10_acceptance_criteria.md`

- 본 design 의 acceptance — 11 doc + patch.md = 12 파일, 한국어, 안전 invariant 명시, 코드 0.
- 각 implementation job 의 공통 acceptance template:
  - `app/agents/<agent>/` 또는 `app/services/<service>/` 안에만 신규 코드.
  - `app.broker.*` import 0 (Broker Gateway 서비스 외).
  - `app.oms.*` 호출 단방향 (Strategy Service 안에서만).
  - typed I/O 검증 테스트.
  - `AgentTrace` 회귀.
  - secret leak 0.
  - LLM optional + fallback 회귀.
  - kill switch 가드 회귀 (engaged 상태에서 새 action 0).
  - 서비스 간 통신은 loopback 한정 회귀.
  - `commit / push / merge / deploy` 자동화 0.

## 5. 횡단 원칙

### 5.1 언어 + 가독성

- 한국어. 기술 식별자 inline `code` 영어.
- 운영자 readable + 개발자 specific.

### 5.2 No fake claims / no time estimates

- 수익 보장 / 승률 / 시간 추정 0.
- Backlog size S/M/L 만.

### 5.3 Safety boundary

- Agent ≠ Broker.
- OMS only executable.
- Broker Gateway only KIS-credentialed.
- LLM not in hard risk block path.
- KIS 미확인값 TODO / fail-closed.
- live default lock.

### 5.4 Existing reference

- `final-platform-plan/00_current_state.md` ~ `10_acceptance_criteria.md` read-only 인용.
- 기존 `app/strategy/`, `app/oms/`, `app/risk/`, `app/broker/`, `app/runtime/`, `app/ops/` 의 모듈 이름 정확히 사용.

### 5.5 No coding

- 실행 가능한 `.py` / `.ts` / SQL / Bash 코드 블록 0.
- pseudocode / ASCII / 도메인 모델 표 OK.

## 6. Codex task 의 절대 제약 (codex-task.md 에 명시)

1. `app/` / `tests/` / `scripts/` / `docs/kis/` / `.env` / `.env.example` / `README.md` / `docs/RUNBOOK.md` / `docs/OPS_AUDIT.md` 어떤 파일도 modify/create/delete 금지.
2. 다른 job 디렉터리 (`final-platform-plan/` 포함) 기존 파일 수정 금지. 참조만 OK.
3. 신규 파일은 `docs/ai/jobs/agent-platform-spec-001/` 안에만 — 11 design doc + patch.md = 12 신규.
4. KIS endpoint / TR_ID / payload / header / response field 새로 만들지 않음. catalog `Confirmed: yes` 행만 인용.
5. 외부 web fetch 없이 작성. 기존 repo 의 code / docs 만 참조.
6. Korean writing.
7. 수익 보장 / 시간 추정 / 거짓 성과 0.
8. 자동 git commit / push / merge / deploy 0.
9. live trading 활성화 / live arm 권고 0.
10. application code 0 line.
11. Broker Gateway 외 다른 서비스가 KIS 자격증명을 보유하는 design 금지.
12. 7 서비스를 외부에 공개하는 endpoint 추가 권고 금지.

## 7. 검증 기준

- 12 파일이 정확히 `docs/ai/jobs/agent-platform-spec-001/` 안에만 생성됨.
- 어떤 doc 도 application 코드 / 테스트 / `.env` / catalog 본문 추가하지 않음.
- 각 doc 이 한국어이며 §4 "필수 포함" 항목 모두 다룸.
- 85 모듈 / 7 서비스 매핑 표가 `01_seven_services.md` 안에 정확히 85 row 로 존재.
- `02_realtime_core_40_agents.md` 가 정확히 40 모듈 다룸.
- `03_news_event_10_agents.md` 가 정확히 10 모듈.
- `04_validation_learning_20_agents.md` 가 정확히 20 모듈.
- `05_ops_security_15_agents.md` 가 정확히 15 모듈.
- `06_top15_focus_set.md` 가 정확히 15 critical + 5 meta-agent 다룸.
- `09_implementation_backlog.md` 가 85 + 7 + 5 = 97 backlog row.
- 수익 보장 / 시간 추정 / KIS endpoint 추측 / live arming 0.
- patch.md 가 12 파일 생성 + 4 카테고리 합계 (40/10/20/15=85) + 7 서비스 매핑 카운트 + 안전 grep 결과 + Claude 검증 prompt + follow-up rule 포함.

## 8. 리뷰 체크리스트

- [ ] §2 산출물 12 개 ↔ 요청 §"산출물" 1:1.
- [ ] §3 의 7 서비스 + Broker Gateway 격리가 design doc 에 반복 명시되도록 §4 강제.
- [ ] §4 의 11 doc design intent 가 4 카테고리 (40/10/20/15) + Top 15+5 + 7 서비스 + LLM + data contracts + backlog + acceptance 모두 커버.
- [ ] §5 횡단 원칙이 일관 적용.
- [ ] §6 Codex 제약이 codex-task.md 에 그대로.
- [ ] §7 검증 기준이 Claude review prompt 와 정합.
- [ ] 본 plan 이 production 코드 / 테스트 / `.env` / catalog 본문 추가 0.

## 9. 본 turn 의 산출물

- [x] `request.ko.md` (85+7 구조).
- [x] `plan.md` (본 파일).
- [ ] `codex-task.md` (다음 step).

본 turn 의 Claude 는 11 design doc 을 직접 작성하지 않는다. Codex 가 다음 turn 에서. application code 0.

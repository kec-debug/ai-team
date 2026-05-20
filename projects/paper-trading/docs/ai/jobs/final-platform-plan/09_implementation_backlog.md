# 09. Implementation Backlog

본 문서는 앞선 design 을 Codex job 으로 변환하기 위한 backlog 이다. 시간 추정은 하지 않고, size 는 S/M/L 로만 표시한다.

## 1. Backlog items

| Job ID | Purpose | Size | 수정 파일 | 신규 파일 | 의존 backlog | Acceptance | Test plan | Risk notes | Rollback notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `paper-runtime-002-training-service` | 24h TrainingRunner 도입 | L | `app/runtime/*` | `app/runtime/training_service.py` | none | start/stop/heartbeat | unit + API | runaway loop | service file revert |
| `paper-domain-001-training-models` | TrainingRun/Tick 모델 | M | `app/domain/*` | model files | none | typed models | model tests | schema churn | remove models |
| `paper-source-001-adapters` | replay/synthetic/live quote source adapter | L | runtime/broker boundary | source package | domain models | source swap | deterministic tests | live source confusion | disable source |
| `paper-session-002-router` | session guard 확장 | M | `app/session/*`, risk | policy docs | domain models | closed session block | session tests | false blocks | policy rollback |
| `agent-001-base` | Agent base abstract + trace contract | M | none or agent package | `app/agents/*` | domain models | no broker import | agent tests | LLM misuse | remove registry |
| `agent-002-seven-agents` | 7 agent 구현 | L | agent package | agent files | agent base | typed outputs | provider tests | weak validation | disable provider |
| `agent-003-llm-provider` | optional LLM provider + fallback | L | agent provider | provider files | agent base | malformed block | mock tests | secret handling | deterministic default |
| `strategy-lab-001-ui` | Strategy Lab UI | M | dashboard/API | static/doc files | strategy registry | strategy list visible | UI tests | scope creep | hide nav |
| `strategy-lab-002-backtest` | backtest endpoint | L | API/runtime | backtest module | source adapters | no broker call | backtest tests | 과장된 결과 해석 | disable endpoint |
| `live-console-001-separated-page` | locked live console page | M | API/static | live console doc/page | ops preflight | read-only locked | TestClient/UI | live confusion | remove route |
| `live-console-002-arm-state-locked` | arm/disarm state design implementation locked | L | ops/API | state module | live console | no order path | state tests | accidental arm | force locked |
| `storage-001-postgres-model` | PostgreSQL schema design implementation | L | storage package | migrations future | data models | persistence tests | migration risk | feature flag off |
| `storage-002-redis-runtime` | Redis heartbeat/locks/idempotency | L | runtime/storage | redis package | training service | idempotency works | integration tests | stale locks | TTL clear |
| `risk-002-advanced-guards` | volatility/disconnect/token guards | M | risk/ops | guard tests | observability | guard visible | risk tests | overblocking | disable guard |
| `observability-001-heartbeat` | heartbeat + status cards | M | runtime/API/UI | heartbeat model | training service | heartbeat visible | API tests | noisy alerts | hide card |
| `observability-002-incident-view` | incident view + audit events | L | API/UI/storage | audit module | storage | recent events | UI/API tests | sensitive payload | redaction gate |
| `reports-002-run-comparison` | run comparison reports | M | reports/API | comparison module | storage | compare runs | report tests | misleading metrics | disable export |
| `ops-002-runbook-sync` | final runbook sync with implementation | S | docs only | docs updates | relevant jobs | docs current | grep review | stale docs | revert docs |
| `soak-002-expanded-scenarios` | longer varied paper soak | M | tests/docs maybe | scenario files | training service | scenario pass | soak tests | nondeterminism | deterministic fixtures |
| `env-001-staging-profile` | staging profile support without live enable | M | config/scripts | docs | ops | safe defaults | config tests | unsafe env | fail-closed |

## 2. Prioritization logic

1. Domain and runtime models before UI.
2. Source adapters before strategy lab backtest.
3. Agent base before individual agents.
4. Storage before incident view and run comparison.
5. Live console remains locked until paper evidence and observability improve.

## 3. Backlog safety rule

Every backlog job must preserve Strategy -> RiskEngine -> OMS -> BrokerAdapter. Any job that needs live activation must be split into plan/review/approval first and cannot be combined with unrelated UI or storage work.

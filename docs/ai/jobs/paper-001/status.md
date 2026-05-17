# Status — paper-001

| Field | Value |
| --- | --- |
| Job ID | paper-001 |
| Title | 내부 paper trading MVP — 확장판 (6개 기능 일괄) |
| Stage | `claude_planning` (옵션 B로 plan 재작성) → **`codex_implementing` 대기** |
| Created (Claude planning) | 2026-05-17 |
| Last update | 2026-05-17 (scope 확장: MARKET + partial + staleness + session + commission + multi-currency) |
| Owner (human) | kec |
| Depends on | api-auth-001 (land 완료), 기존 PaperBroker/OMS/RiskEngine/PortfolioService skeleton (mvp-001..mvp-022) |
| Blocks | `paper-002` (시장가 시뮬레이션), `paper-003` (partial fill / slippage), `api-market-data-001` (실 quote 연결, 본 MVP의 Quote 주입 채널을 사용) |

## 산출물

| 파일 | 상태 |
| --- | --- |
| `docs/ai/jobs/paper-001/plan.md` | done |
| `docs/ai/jobs/paper-001/codex-task.md` | done |
| `docs/ai/jobs/paper-001/status.md` | done (본 파일) |
| `docs/ai/jobs/paper-001/patch.md` | **pending** (Codex 작성) |
| `docs/ai/jobs/paper-001/review.md` | **pending** (Claude 작성) |

## 안전 invariant (계획 단계)

본 plan/codex-task는 다음을 명시적으로 보장:

- **Paper가 기본**, **live 비활성** 유지 (`live_trading_enabled` 기본 False).
- **LLM/Agent의 broker 직접 호출 경로 추가 0건**.
- **추천 agent는 `OrderIntent`(non-executable)만** — `BrokerOrder` 생성은 OMS만.
- **모든 주문은 Strategy → RiskEngine → OMS → PaperBroker 통과** — 본 job은 OMS/Risk 본문 미접촉.
- **실 broker API 호출 0건** — KIS/Alpaca client 본문 미접촉.
- **실 API key 0건** — 테스트는 fake 값만.
- **`.env` 읽기/수정 0건** — `.env.example`에 변수 이름 + 한 줄 설명만 추가.
- **시장가 주문 도입 0건** — `OrderType.MARKET` 부재 유지. 시장가 시뮬레이션은 `paper-002` 후보.
- **GUI 미접촉** — `app/api/`, `app/static/`, `app/main.py` 변경 0건. dry-run 모듈도 미접촉.
- 자동 git commit / push / merge / deploy 0건.

## 핵심 설계 결정 (확장 후)

- **`OrderType.MARKET`** 새 enum 멤버. 3중 가드(`ALLOW_PAPER_MARKET_ORDERS=true` + PAPER + !live)로 RiskEngine 승인. MARKET fill at `quote.ask`/`quote.bid`, slippage 0.
- **`PaperBroker.tick(quote)`** — quote 입력 시 LIMIT/STOP_LIMIT/MARKET 매치 + staleness 검사 + session 검사 + partial fill(`floor(quote.volume * 0.05)`).
- **`PaperAccount.cash: dict[currency, Decimal]`** — multi-currency 분리 보관. FX 변환 0건. 통화별 분리 보고.
- **`PortfolioSnapshot`의 PnL/market_value가 `dict[currency, Decimal]` 시그니처** — 기존 단일 Decimal 사용처 갱신 필요 (test_portfolio_service 등).
- **`Quote`에 `session: Session | None`, `currency: str = "USD"` 추가** — 기존 코드는 default로 backward compatible.
- **`PaperJournal`** — orders + trades 메모리 default. `PAPER_LOG_DIR` 설정 시 JSONL append. entry에 `currency` 보존.
- **`PaperEngine`** — `submit_intents` + `on_quote` 두 메서드로 사이클 완결.
- **Commission** — `quantity * PAPER_COMMISSION_PER_SHARE + PAPER_COMMISSION_PER_FILL`. 기본 `0.005 / share`.

### Scope 경고

본 plan은 6개 기능을 한 job에 모두 담는다. 예상 규모 약 **1100 LoC + 60+ 테스트**. Codex 한 pass로 가능하지만 review 부담이 크다. 사용자가 "하나로 진행"으로 결정 — paper-001-mc / paper-002 분할 옵션은 사용 안 함.

## 다음 단계

1. **Codex 호출** — GUI `Codex 구현 실행` 버튼 또는 tmux `ai-team:codex`에서 `prompts/codex-implementer.md` 적용 + 본 폴더의 `plan.md` + `codex-task.md` 읽게 함.
2. Codex가 `patch.md` 작성. 안전 grep + 테스트 결과 + commit-skip 확인 기록.
3. **Claude 리뷰** — `git diff` + `patch.md` 검토 → `review.md` 작성 (`APPROVE` / `REQUEST CHANGES` / `BLOCK`).
4. **사람** — `git status` / `git diff` 직접 확인 후 staging/commit. commit 시 plan §3의 파일 목록만.

## 사람이 미리 결정할 만한 사항

- [ ] **시장가 시뮬레이션을 본 MVP에 포함할지** — 현재 plan은 LIMIT/STOP_LIMIT만. 사용자 요청에 "Basic market/limit order simulation"이라고 적힌 부분을 LIMIT-only로 해석. 시장가 포함 원하면 plan 승인 전에 알려달라. (별 job `paper-002`로 분리 권장.)
- [ ] **Quote 소스** — 본 MVP는 caller가 `Quote`를 직접 주입. 실 시세 연결은 `api-market-data-001`(KIS 현재체결가, KIS_1 catalog 활용)에서.
- [ ] **`PAPER_LOG_DIR` 영속화 사용 여부** — 기본 off. on하면 디스크 라인 생성, 운영 환경에서 디렉터리 관리 필요.

## 사람 액션 아이템 (계획 단계에서 미리)

- [ ] 직전 채팅에서 노출된 KIS Developers 포털 로그인 비번이 아직 그대로면 변경. paper-001 자체는 KIS와 무관하지만 보안 hygiene 차원.
- [ ] 워크트리 dirty 상태 확인 — `git status`로 본 job 시작 전 정리할지 결정. 기존 untracked 산출물(KIS_1/api-auth-001/mvp-022 등)이 commit되지 않은 채 남아 있을 가능성 있음.

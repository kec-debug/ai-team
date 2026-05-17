# Codex 호출 프롬프트 — paper-001

> 이 파일은 사용자가 Codex 세션에 붙여 넣는 **task 메시지**다. `prompts/codex-implementer.md`(role prompt)가 이미 적용돼 있다고 가정한다.
>
> 사용 방법: 아래 `=== PROMPT START ===` ~ `=== PROMPT END ===` 사이를 그대로 복사해 tmux `ai-team:codex` 창 또는 GUI의 Codex 입력에 붙여 넣는다.

---

=== PROMPT START ===

Job: **paper-001**
Project directory: `/root/ai-dev-center/projects/ai-team`
Paper-trading subproject: `/root/ai-dev-center/projects/ai-team/projects/paper-trading`

먼저 다음 파일을 순서대로 읽어라:

1. `docs/ai/jobs/paper-001/plan.md` — Claude의 구현 계획 (배경, 범위, scope 경고, 6개 기능 명세).
2. `docs/ai/jobs/paper-001/codex-task.md` — Phase 1~8로 나뉜 byte-level 구현 본문 (이게 너의 실제 작업서).

그 다음 `docs/ai/jobs/paper-001/codex-task.md`의 Phase 1~8을 **순서대로** 적용한다.

## 작업 범위 (요약)

6개 기능을 한 job에 land하는 내부 paper trading MVP 확장판:

1. LIMIT / STOP_LIMIT / **MARKET** 시뮬레이션 (MARKET은 3중 가드 통과 시만).
2. **Partial fill** (`floor(quote.volume * PAPER_MAX_FILL_RATIO_OF_VOLUME)` cap, 잔량 누적).
3. **Quote staleness** 검사 — `PaperBroker.tick()`이 책임. `quote.is_stale(now, max_age_seconds)` 호출.
4. **Session 검사** — `quote.session`이 `_allowed_sessions`에 없으면 fill 0건.
5. Cash + Realized/Unrealized PnL — `PaperAccount` 신규 + `PortfolioService` 확장.
6. **Multi-currency** — `PaperAccount.cash`가 `dict[currency, Decimal]`. **FX 변환 0건.** 통화별 분리 보관·보고.

Phase 1~8 구체 본문은 codex-task.md에 박혀 있으니 거기를 byte-level 따르고, 아래는 핵심 invariant만 재요약:

## Hard rules (위반 시 BLOCKED)

- `OrderType.MARKET` 도입 시 RiskEngine은 **3중 가드** 통과해야 승인:
  `ALLOW_PAPER_MARKET_ORDERS=true` AND `TradingMode=PAPER` AND `live_trading_enabled=False`. 하나라도 깨지면 reject.
- 기존 `ALLOW_MARKET_ORDERS=true` 거절(load_settings)은 **그대로 보존**. 새 flag는 `ALLOW_PAPER_MARKET_ORDERS` (별개).
- **FX 변환 / 환율 적용 0건**. `equity_total_in_base_currency`, `to_base_currency`, `exchange_rate` 같은 함수/상수 도입 금지. 통화별 분리만.
- `PortfolioSnapshot`은 **기존 단일 Decimal 필드 보존**(`realized_pnl`, `market_value`, `unrealized_pnl`) + 신규 `_per_currency: dict[str, Decimal]` 3개 필드 추가. 단일 필드는 `app/api/routes.py`가 직접 읽고 있어 후방호환 필수.
- 외부 HTTP lib(`requests`, `httpx`, `aiohttp`, `urllib3`) import 금지. stdlib만.
- `.env` 읽기/수정 금지. `.env.example`은 신규 변수 **이름 + 한 줄 설명만** (값/placeholder 0건).
- 실 app key / app secret / access token / 계좌번호 / refresh token 어디에도 기록 금지. 테스트는 `"fake-*"` 또는 8자리 이하 fake 숫자만.
- live trading 활성화 / 실주문 / RiskEngine 우회 / OMS 우회 / Strategy의 broker 직접 호출 / LLM의 broker 직접 호출 추가 금지.
- 자동 `git commit` / `push` / `merge` / `deploy` 금지.

## 절대 만지지 말 것 (파일 단위)

- `app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*` — GUI 미접촉.
- `app/runtime/dry_run.py`, `app/runtime/dry_run_report.py`, `app/runtime/paper_runner.py` — dry-run 미접촉.
- `app/strategy/*` — Strategy 본문 미접촉.
- `app/oms/manager.py` — OMS 본문 미접촉.
- `app/broker/base.py`, `app/broker/alpaca_paper.py`, `app/broker/kis.py`, `app/broker/kis_http.py`, `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py` — broker 어댑터 본문 미접촉.
- `.env`, `.gitignore`, `docs/kis/*`, `docs/ai/MASTER_TRADING_ROADMAP.md`, `prompts/*`, `scripts/*`, `imports/*`, 이전 mvp 산출물 미접촉.

(예외: `app/risk/engine.py`는 Phase 5에서 MARKET 분기 추가만 허용. `app/portfolio/service.py`는 Phase 2에서 시그니처 확장만.)

## 적용 후 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기대: 기존 242 PASS + 신규 약 60+ PASS, 회귀 0건, 외부 네트워크 호출 0건.

## 안전 grep (적용 후 반드시 실행, patch.md에 결과 기록)

```bash
cd /root/ai-dev-center/projects/ai-team
git diff -- projects/paper-trading/ | grep -E "FX|exchange_rate|to_base_currency|equity_total_in_base" || echo "fx-grep: clean"
git diff -- projects/paper-trading/ | grep -E "import requests|import httpx|import aiohttp|import urllib3" || echo "http-lib-grep: clean"
git diff -- projects/paper-trading/ | grep -E "PSNFD|PKID|AKIA|sk-|ghp_|Bearer eyJ|appkey=|appsecret=|\b\d{10,}\b" || echo "secret-grep: clean"
git diff --stat -- projects/paper-trading/app/api/ projects/paper-trading/app/static/ projects/paper-trading/app/main.py | grep -v '^$' && echo "GUI changed — BLOCK" || echo "gui-grep: clean"
git diff --stat -- projects/paper-trading/app/runtime/dry_run.py projects/paper-trading/app/runtime/dry_run_report.py projects/paper-trading/app/runtime/paper_runner.py | grep -v '^$' && echo "dry_run changed — BLOCK" || echo "dry-run-grep: clean"
git diff --stat -- projects/paper-trading/app/broker/kis.py projects/paper-trading/app/broker/kis_http.py projects/paper-trading/app/broker/kis_token_cache.py projects/paper-trading/app/broker/kis_quote_mapper.py projects/paper-trading/app/broker/alpaca_paper.py projects/paper-trading/app/broker/base.py | grep -v '^$' && echo "kis/alpaca/base changed — BLOCK" || echo "kis-grep: clean"
```

6개 라벨 전부 `clean`이 출력돼야 함. 하나라도 BLOCK이면 작업 중단 + patch.md에 BLOCKED 사유 기록 + 변경 되돌리기.

## 산출물: `docs/ai/jobs/paper-001/patch.md`

다음 9개 섹션을 codex-implementer 역할의 표준 5섹션 형식 위에 확장해서 작성:

1. **Files Changed** — plan §3의 파일 목록과 일치하는지 확인.
2. **Implementation Summary** — Phase 1~8 각각 무엇을 어떻게 적용했는지.
3. **Safety Confirmation** — 위 Hard rules 항목별 ✓ 체크.
4. **Test Results** — `compileall` 결과 + `pytest` 전체 수치 (기존 242 + 신규 N).
5. **Remaining TODOs** — partial fill에서 다중 fill 시퀀스 테스트 보강, paper-001-gui 등 후속.
6. **Phase별 적용 요약** — Phase 1: enum/orders/quote/fills, Phase 2: portfolio service, Phase 3: PaperAccount, Phase 4: PaperBroker tick, Phase 5: RiskEngine MARKET, Phase 6: journal+engine, Phase 7: config+env+README, Phase 8: tests.
7. **신규 도메인/클래스/메서드 명단** — `OrderType.MARKET`, `Fill`, `PaperAccount`, `PaperAccountError`, `PaperJournal`, `OrderLogEntry`, `TradeLogEntry`, `PaperEngine`, `PaperBroker.tick`, `PaperBroker.cancel_all`, `PortfolioSnapshot._per_currency` fields, etc.
8. **안전 grep 결과** — 위 6개 명령의 `clean` 출력 그대로.
9. **commit/push/merge/deploy 미실행 확인.**

마지막에 `READY FOR REVIEW` 또는 `BLOCKED` (사유).

## 작업 시작 신호

위 내용 이해했으면 다음 순서로 시작:

1. plan.md, codex-task.md 읽기 보고 (간단히).
2. 워크트리 현재 상태 `git status` 확인 (현재 깨끗하다고 기대).
3. Phase 1부터 순차 적용. 각 Phase 끝에 변경 파일 명시.
4. Phase 8 끝나면 위 검증 명령 실행.
5. patch.md 작성 및 verdict.

진행 중 의문이 생기면 plan.md / codex-task.md 본문을 인용해서 결정. 본문에 없는 결정은 fail-closed 쪽으로 보수적 선택.

`git commit` / `push` / `merge` / 배포는 **절대 실행하지 않는다.** 변경만 워크트리에 남기고 종료.

=== PROMPT END ===

---

## 사용 방법

1. tmux `ai-team:codex` 창 열기 (또는 GUI에서 Codex 입력 영역).
2. role prompt `prompts/codex-implementer.md`가 이미 세션에 적용돼 있는지 확인. 안 됐으면 먼저 적용.
3. 위 `=== PROMPT START ===` ~ `=== PROMPT END ===` 사이를 복사해 붙여 넣고 전송.
4. Codex가 plan.md / codex-task.md를 읽고 Phase 1부터 시작.
5. 끝나면 `docs/ai/jobs/paper-001/patch.md`가 생성됨 + Codex가 `READY FOR REVIEW` 또는 `BLOCKED` 보고.
6. 그 결과를 Claude(나)에게 알려 주면 `review.md` 작성 진행.

## 옵션: GUI 버튼으로 호출

GUI(`http://127.0.0.1:3100`)의 `Codex 구현 실행` 버튼이 자동으로 `prompts/codex-implementer.md` 적용 + job 폴더 인식을 처리한다면 위 task 메시지를 별도 붙여 넣을 필요가 없을 수 있다. GUI 동작은 `docs/ai/CLAUDE_CODEX_WORKFLOW.md` 참고. 필요시 GUI가 Codex 입력 영역에 박는 default prompt를 위 본문으로 수동 교체.

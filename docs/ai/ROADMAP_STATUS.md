# Roadmap Status — paper-trading 프로젝트

> 마지막 갱신: 2026-05-15 (roadmap-status-fix)
> 참고: 본 문서가 "지금 어디까지 왔는가?"의 단일 source of truth. 새 작업 시작 전 반드시 본 문서 + `MASTER_TRADING_ROADMAP.md` + 기존 `docs/ai/jobs/*` 확인.

---

## 🎯 Next single action

**사용자가 `docs/kis/MISSING_MARKET_DATA_VALUES.md`의 `<TBD>` 항목을 KIS 공식 개발자 포털에서 직접 채운다.**

- 채워야 할 핵심 값: 모의투자 base URL, 현재가 endpoint path, HTTP method, 필수 headers, TR ID(모의투자용), request query/body fields, response 필드 이름(last/bid/ask/volume/timestamp), 거래소 코드, 호가단위, timezone, rate limit.
- 채워 넣은 뒤 각 행의 `Confirmed: no` → `Confirmed: yes`로 변경.
- 모두 채워지면 mvp-023의 HTTP 부분(즉 `KisMarketDataClient.get_quote`와 `kis_raw_quote_to_domain`) 재개 가능. **새 mvp 번호로 만들지 말고 mvp-023 슬롯 안에서 재개.**

**차선 (사용자가 KIS 문서값 확보에 시간이 필요한 경우):**
- mvp-024를 `source="synthetic"` mock 데이터로 시작. **반드시 "로컬 검증용 — KIS 실제 HTTP 대체 아님"으로 표시.** 후속에서 실 KIS 데이터 land 시 source 교체.

---

## 📊 전체 진행 현황

### Foundation (Phase 0) — 누적 land, tests pass

```
mvp-001..002  → README / GUI 정리                                   ✅ 완료 (commit 진행 사항은 사용자)
mvp-003       → paper-trading 스캐폴드 첫 시도 (BLOCKED 후 mvp-005가 absorb)  ↩️ DEPRECATED
mvp-004       → AI dev team GUI 레이아웃                             ✅ 완료
mvp-005       → paper-trading 골격 + premarket gap 전략               ✅ 완료
mvp-006       → KIS_PAPER_* 명명 시도 (mvp-006-1이 KIS_*로 대체)        ↩️ DEPRECATED
mvp-006-1     → KIS 설정 + BrokerAdapter skeleton (KIS_* 표준)         ✅ 완료
mvp-007       → KisAuth/Account/MarketData sub-clients               ✅ 완료
mvp-008       → KIS pre-flight + dry_run (mvp-009가 absorb)           ↩️ DEPRECATED
mvp-009       → KisOrderRequest/Response + sanitize + capabilities    ✅ 완료
mvp-010, 011-013  → KIS HTTP 반복 시도 (공식값 부재로 fail-closed)      ↩️ DEPRECATED
mvp-014-017   → MISSING_OFFICIAL_VALUES.md catalog (구조적 deferral)    ✅ 완료
mvp-018       → DryRunController + 리포트 파일 + 4 API + kill switch    ✅ 완료
mvp-019       → analyzer + analysis_summary/report/claude_review_input ✅ 완료
mvp-020       → 7개 helper shell scripts + safe env enforcement        ✅ 완료
mvp-021       → /dashboard 브라우저 UI (read-only safe buttons)        ✅ 완료
mvp-022       → .env 자동 로딩 (CWD 무관) + override=False              ✅ 완료
```

**누적 결과**: pytest **214 passed**. 도메인/OMS/Risk/Broker/Strategy 격리 유지. live trading 차단 6단 + KIS endpoint 추측 금지 + 외부 HTTP 라이브러리 import 0건 + raw credentials 노출 0건.

### Roadmap mvps (활성 영역)

| Roadmap slot | 작업명 | 상태 | 비고 |
| --- | --- | --- | --- |
| **mvp-023** | KIS 실제 시세 조회 연결 | ⏳ **BLOCKED-BY-DOCS** | Quote 도메인 + mapper skeleton + MISSING_MARKET_DATA_VALUES catalog 완료. HTTP 호출 부분만 공식값 대기. |
| mvp-024 | 실제 시세 기반 종목 후보 생성 | ⏸️ 미시작 | mvp-023 HTTP unblock 또는 synthetic source 시작 |
| mvp-025 | Strategy/RiskEngine/OMS/dry-run flow 검증 | ⏸️ 미시작 | mvp-024 candidates 필요 |
| mvp-026 | KIS 모의투자 주문 HTTP 연결 | ⏸️ 미시작 (KIS 주문 endpoint 공식값 부재 — BLOCKED 예상) | `MISSING_OFFICIAL_VALUES.md` §4 채워야 unblock |
| mvp-027 | 장시간 모의투자 검증 | ⏸️ 미시작 | mvp-024..026 land 후 |
| mvp-028 | 결과 리포트 / 승률 / 손익비 분석 | ⏸️ 미시작 | mvp-027 데이터 누적 후 |
| mvp-029 | 소액 live validation 준비 | ⏸️ 미시작 | 모든 이전 단계 통과 + 명시적 사용자 승인 |

---

## 🚫 BLOCKED 상세

### mvp-023 BLOCKED-BY-DOCS

**Blocker**: KIS Open API 시세 조회의 공식 endpoint / TR ID / request fields / response fields 값이 본 저장소에 없음. Codex는 외부 웹 접근이 없음.

**완료된 부분 (BLOCKED와 무관, 보존)**:
- `app/domain/quote.py` — broker-agnostic Quote 모델 (frozen dataclass + invariants + spread_pct + is_stale).
- `app/broker/kis_quote_mapper.py` — `kis_raw_quote_to_domain(raw, symbol, source)` skeleton with NotImplementedError.
- `docs/kis/MISSING_MARKET_DATA_VALUES.md` — 4섹션 catalog (현재가 endpoint / Quote 응답 매핑 / 호가단위·거래소 시간 / 시세 종류·권한). 모두 `<TBD>` + `Confirmed: no`.
- 신규 테스트 ~20개 PASS.

**Unblock 조건**: 사용자가 KIS 공식 개발자 포털에서 `<TBD>` 항목을 채우고 `Confirmed: yes`로 표시. 그 뒤 mvp-023 슬롯 안에서:
1. `kis_quote_mapper.kis_raw_quote_to_domain` 본문 구현.
2. `KisMarketDataClient.get_quote` 실제 HTTP 호출 추가 (단 `KisHttpClient.request`는 여전히 외부 HTTP 라이브러리 import 가드 유지 필요 — 정식 HTTP 사용 시 별도 결정).
3. 회귀 테스트.

**Unblock 안 됨 시 차선**: mvp-024 synthetic 시작 (아래 참고).

### mvp-026 잠재적 BLOCKED-BY-DOCS

KIS 모의투자 주문 endpoint 공식값(`MISSING_OFFICIAL_VALUES.md` §4)도 미확정. mvp-026 진입 시점에 동일 BLOCKED 가능성 매우 높음. mvp-026 시작 전 사용자가 주문 endpoint도 함께 확인하면 효율적.

---

## ↩️ DEPRECATED / 중복 작업

| mvp 폴더 | 상태 | 흡수/대체 | 안전 영향 |
| --- | --- | --- | --- |
| `mvp-003/` | 미실행 첫 시도 | `mvp-005/`가 absorb | 0 (코드 land 안 됨) |
| `mvp-006/` | KIS_PAPER_* 명명 | `mvp-006-1/` KIS_* 표준이 대체 | 0 (코드 land 안 됨) |
| `mvp-008/` | KIS pre-flight 첫 시도 | `mvp-009/`가 absorb | 0 (plan만 작성) |
| `mvp-010/` | KIS HTTP 시도 | `mvp-014-017-bundle/`이 구조적 deferral로 정리 | 0 |
| `mvp-011-013-bundle/` | KIS HTTP 반복 시도 | 동상 | 0 |
| `mvp-008-import/` | 임시/실험 폴더 | 무시 | 0 |
| `mvp-01/` | 폴더명 typo (`mvp-001`과 별개로 존재) | 무시 또는 정리 | 0 |
| `mvp-002~/` | 임시/실험 폴더 | 무시 | 0 |

**중복 패턴 분석**: KIS HTTP 영역에서 mvp-006/008/010/011-013/014-017이 같은 작업("공식값 없는 KIS HTTP 구현 시도")을 반복함. mvp-014-017-bundle이 "MISSING_OFFICIAL_VALUES.md catalog"라는 올바른 해법을 정착시켰음. 이후 mvp-023도 같은 패턴(시세 전용 catalog)을 채택해 일관됨.

---

## ✅ 안전 불변식 (현재 land된 상태 기준)

- `OrderType.MARKET` 부재. 시장가 주문 코드 경로 0건.
- `LIVE_TRADING_ENABLED` 6단 차단(`Settings` 기본 False + `load_settings()` env 차단 + `RiskEngine.evaluate` reject + `OMS.place` 차단 + `POST /paper/run` 503 + `KisBroker.__init__` KIS_ENV reject).
- `ALLOW_MARKET_ORDERS=true` → `load_settings()` ValueError.
- `KIS_ORDER_DRY_RUN=true` 기본값. KisBroker.place_order이 dry_run 시 OrderAck(status="dry_run") 반환, false 시 NotImplementedError.
- 외부 HTTP 라이브러리(`requests`/`httpx`/`aiohttp`/`urllib3`) import 0건 전 저장소.
- KIS endpoint URL / TR ID / payload / response field 이름 코드 0건. `<TBD>` placeholder만 catalog 문서에.
- `Settings`의 KIS 비밀 3필드 `field(repr=False)` 마스킹. `KisBroker`/sub-client `__repr__` 마스킹.
- `/paper/status` 응답에 raw credentials 0건 (`account_no_masked` + `secret_exposed: false`).
- Strategy 패키지가 `app.broker.kis*` import 0건. Strategy/Agent/LLM이 broker 직접 호출 불가.
- `/dashboard`이 read-only safe endpoint만 호출 (`<form>` 0건, `/paper/run` 호출 0건, 실주문/시장가/live 토글 0건).
- `scripts/_common.sh`이 4개 안전 env force export (shell이 `.env`보다 우선).
- `reports/` 프로젝트 `.gitignore`로 무시.
- `dump_safe()`가 모든 리포트 dict에서 credential 키 이름 substring 거절.

---

## 📜 새 mvp 번호 생성 금지 원칙

앞으로:

1. **새 mvp 번호 만들지 말 것** (예: mvp-024-1, mvp-030, mvp-023-fix). 작업이 기존 roadmap slot(mvp-023..mvp-029) 중 어디에 매핑되는지 먼저 결정.
2. **매핑할 slot이 없으면**: 그 작업이 정말 로드맵에 필요한지 재검토. roadmap에 누락된 항목이면 `MASTER_TRADING_ROADMAP.md`를 먼저 수정.
3. **BLOCKED 상태는 새 번호 대신 BLOCKED 표시**. 같은 slot 안에서 "재개 가능 조건"을 명시.
4. **Codex 구현 지시 만들기 전**:
   - `ROADMAP_STATUS.md`(본 문서)에서 해당 slot 상태 확인.
   - `MASTER_TRADING_ROADMAP.md`에서 slot 정의 확인.
   - `docs/ai/jobs/<slot>/` 폴더에서 기존 plan/codex-task/patch/review 확인.
   - 중복이면 새 작업 만들지 말고 기존 자료 업데이트.
5. **공식 KIS 문서값 부재**: KIS HTTP 코드 추가 작업 금지. 대신 `MISSING_*` catalog 확장 또는 보류.
6. **mock/synthetic 데이터** 사용 시: 명시적 명명 (`synthetic` / `mock`) + `Quote.source` 라벨 + "로컬 검증용" 문서 표시. KIS 실제 HTTP 대체로 표현 금지.

---

## 📚 참고 문서

- `docs/ai/MASTER_TRADING_ROADMAP.md` — 전체 로드맵 + Claude/Codex 협업 방식 + 중복 방지 규칙.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` — KIS 전반(OAuth/계좌/시세/주문) 누락 값 catalog (mvp-014-017-bundle).
- `docs/kis/MISSING_MARKET_DATA_VALUES.md` — 시세 전용 누락 값 catalog (mvp-023).
- `docs/ai/CLAUDE_CODEX_WORKFLOW.md` — Claude + Codex 워크플로.
- `docs/ai/jobs/mvp-023/` — mvp-023 최신 plan/codex-task/patch/review.
- `projects/paper-trading/README.md` — 운영 가이드.

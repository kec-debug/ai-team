# roadmap-status-fix — 정리 plan

> 작성: 2026-05-15. Claude 분석 단독. Codex 구현 지시 없음.

## 1. 요청 요약

지금까지 mvp 번호(mvp-001 ~ mvp-023)가 누적되면서:
- KIS HTTP 시도가 여러 번 반복됨(공식 문서값 부재 상태에서).
- 같은 영역이 mvp-006 → mvp-006-1, mvp-008 → mvp-009 등으로 갈아엎히면서 중복 발생.
- mvp-023이 "완료"인지 "BLOCKED"인지 한 줄로 표현되지 않음.
- "다음에 뭘 해야 하나?" 질문에 단 하나의 답이 없음.

본 작업은 **코드 변경 0건**. 문서 3개 생성/업데이트로 진행 상태 단일 source of truth 확보.

## 2. 진단

### 2.1 핵심 분류

**Phase 0 — Foundation (✅ 완료, 이미 land + tests pass)**

mvp-005 / mvp-006-1 / mvp-007 / mvp-009 / mvp-018 / mvp-019 / mvp-020 / mvp-021 / mvp-022 — paper-trading 골격, KIS 설정/skeleton, dry-run runner, analyzer, helper scripts, dashboard UI, `.env` 자동 로딩. 모두 review APPROVE 받음.

**Roadmap mvp-023 — 시세 조회 연결 (⏳ BLOCKED-BY-DOCS)**

- Quote 도메인 모델 + KIS quote mapper skeleton + MISSING_MARKET_DATA_VALUES catalog = **완료**.
- KIS 시세 HTTP 호출 = **BLOCKED** — 공식 endpoint/TR ID/response 필드 부재.
- 사용자 액션: `docs/kis/MISSING_MARKET_DATA_VALUES.md`의 `<TBD>` 항목을 KIS 공식 개발자 포털에서 채워야 unblock.

**Roadmap mvp-024 ~ mvp-029 — 미시작**

- mvp-024 (candidate generation): mvp-023의 `Quote` 모델을 입력으로 사용. 실 KIS 데이터 또는 `source="synthetic"` mock 둘 다 가능.
- mvp-025 (Strategy → RiskEngine → OMS → dry-run flow): mvp-024 candidate가 있어야 의미 있음.
- mvp-026 (KIS paper order HTTP): BLOCKED-BY-DOCS (주문 endpoint 부재).
- mvp-027 (long verification): mvp-024/025/026 land 후 진행.
- mvp-028 (performance analysis): 충분한 dry-run 데이터 누적 후.
- mvp-029 (live validation prep): 모든 이전 단계 통과 후 명시적 사용자 승인.

### 2.2 중복 / 폐기된 작업

| 작업 | 상태 | 흡수/대체 |
| --- | --- | --- |
| mvp-006 | DEPRECATED | mvp-006-1이 흡수 (`KIS_PAPER_*` → `KIS_*` 명명 통일) |
| mvp-008 | DEPRECATED | mvp-009가 흡수 (pre-flight + KisOrderRequest/Response + capabilities) |
| mvp-010, mvp-011-013-bundle | DEPRECATED | mvp-014-017-bundle이 구조적 deferral로 정리 (MISSING_OFFICIAL_VALUES.md catalog) |
| mvp-003 (paper-trading scaffold 시도) | DEPRECATED | mvp-005가 absorb |
| mvp-008-import, mvp-002~ | 임시/실험 폴더 | 무시 |

### 2.3 KIS HTTP 반복 시도 분석 (재발 방지)

mvp-006/006-1/007/008/009/010/011-013-bundle/014-017-bundle/mvp-023 — 모두 KIS Open API HTTP 연결 시도. 결과:
- 모든 시도가 공식 문서값 부재로 `NotImplementedError` fail-closed에 도달.
- mvp-014-017-bundle이 "구조적 deferral"의 모범 — MISSING catalog 생성.
- mvp-023이 같은 패턴(시세 전용 MISSING catalog).
- **교훈**: 공식 문서값이 repo에 들어오기 전까지 KIS HTTP "구현" 시도는 재생산하지 말 것.

## 3. 산출물 (이 task에서 만드는 것)

### 3.1 신규/수정 문서

| 파일 | 동작 | 내용 |
| --- | --- | --- |
| `docs/ai/ROADMAP_STATUS.md` | 신규 | 전체 진행 현황 단일 source of truth |
| `docs/ai/MASTER_TRADING_ROADMAP.md` | 업데이트 | 현재 상태 반영 + 중복 방지 규칙 신설 |
| `docs/ai/jobs/roadmap-status-fix/plan.md` | 신규 (이 문서) | 정리 작업 자체 기록 |
| `docs/ai/jobs/roadmap-status-fix/request.ko.md` | 신규 | 사용자 요청 보존 |

**코드 변경 0건.** 새 mvp 번호 0개 생성. Codex 구현 task 0개 생성.

### 3.2 출력에 절대 포함하지 않을 것

- 실제 KIS app key / app secret / 계좌번호 / token.
- 실제 KIS endpoint URL / path / TR ID / payload.
- `.env` 내용 인용.

## 4. 핵심 결정

### 4.1 mvp-023 분류

**BLOCKED-BY-DOCS** (완료 아님, 폐기 아님). 부분 산출물(Quote 모델, mapper skeleton, MISSING catalog)은 완료 상태로 보존하되 HTTP 연결은 미완료. 사용자가 KIS 공식 문서값을 `MISSING_MARKET_DATA_VALUES.md`에 채우면 같은 mvp-023 슬롯에서 HTTP 부분만 재개. 새 mvp 번호로 이동하지 않음.

### 4.2 새 mvp 번호 생성 금지 원칙

앞으로 새 작업이 필요하면:

1. Roadmap의 mvp-023..mvp-029 slot 중 하나에 매핑.
2. 매핑할 slot이 없으면 — 그 작업이 정말 로드맵에 필요한지 재검토.
3. 새 번호(mvp-024-1, mvp-024-fix 등) 생성 금지.
4. BLOCKED-BY-DOCS 상태는 새 번호 대신 같은 slot 안에서 "재개 가능 조건" 명시.

### 4.3 "단 하나의 다음 작업"

`ROADMAP_STATUS.md`의 "Next single action" 섹션에 명시. 본 시점 권고: **사용자가 `docs/kis/MISSING_MARKET_DATA_VALUES.md`의 `<TBD>` 항목을 KIS 공식 문서에서 채운다** (mvp-023 HTTP 부분 unblock). 채우기 어려우면 차선: mvp-024를 `source="synthetic"` mock 데이터로 시작 (로컬 검증용으로 명시).

### 4.4 mock/synthetic 데이터 명명 규칙

mvp-024 또는 후속에서 mock/synthetic 데이터를 사용할 경우:
- 패키지/모듈 이름에 `synthetic`/`mock` 명시 (예: `app/marketdata/synthetic_quotes.py`).
- `Quote.source` 필드를 `"synthetic"`/`"mock"`으로 명시.
- 문서에 "로컬 검증용 — KIS 실제 HTTP 대체 아님" 명시.
- `/paper/status`에 데이터 source flag 표시.
- 향후 실 KIS 데이터 land 시 source 교체로 마이그레이션.

## 5. 검증

문서만 만드므로 `pytest`로 검증할 항목 없음. 다만 다음 정성 검증:

- [ ] `ROADMAP_STATUS.md`에 mvp-001..mvp-023 매핑 표 존재.
- [ ] mvp-023 = BLOCKED-BY-DOCS로 표시됨.
- [ ] "단 하나의 다음 작업"이 명시됨.
- [ ] `MASTER_TRADING_ROADMAP.md`에 중복 방지 규칙이 §10 (또는 신규 섹션)으로 추가됨.
- [ ] 새 mvp 번호 0개 생성.
- [ ] Codex 구현 지시 task 파일(codex-task.md, patch.md) 0개 생성.
- [ ] 실제 KIS 값(endpoint, key, secret, account) 어떤 문서에도 미포함.

## 6. 끝맺음 — Codex 프롬프트

본 작업 자체는 Claude 단독이지만, 사용자가 마지막에 Codex 창에서 같이 처리할 수 있도록 **light verification-only 프롬프트**를 chat 응답 끝에 제공한다. 이 프롬프트는:

- 코드 변경 0건 (verification만).
- 새 KIS HTTP 코드 추가 금지 재확인.
- 기존 pytest 214 PASS 유지 확인.
- 새 mvp 번호 생성 금지 확인.
- `ROADMAP_STATUS.md` 존재 확인.

Codex가 이 prompt를 실행해도 BLOCKED-BY-DOCS 상태가 풀리지 않으며, 사용자 액션(KIS 공식값 채우기)이 진짜 다음 단계임.

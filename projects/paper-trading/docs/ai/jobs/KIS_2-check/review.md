# KIS_2-check — Claude Review

## Verdict

APPROVE (with notes for the next-job plan)

본 audit 는 코드/도메인 catalog/`.env`/GUI 어디도 건드리지 않았고, KIS_2 의 §4 paper-supported 행 분류가 정확하다. 다음 job 의 scope 권고 ("`api-orders-paper-002-cancel-replace` 로 분리") 도 catalog 의 BLOCKED 상태와 어댑터 구조 양쪽에서 타당하다. 단 §6 의 minor design gap 을 다음 job 의 plan 단계에서 명시적으로 해소해야 한다.

본 review 는 author (Claude) 가 직접 작성한 audit 를 second pass 로 점검한 결과다. self-rubber-stamp 방지를 위해 catalog 행을 직접 재검증했고, 두 가지 minor design gap 을 추가로 식별했다.

## Summary of artifacts

- `docs/ai/jobs/KIS_2-check/plan.md` — full audit (요청 §1~§9 모두 포함).
- `docs/ai/jobs/KIS_2-check/recommendation.md` — condensed status + next-job 권고.
- `docs/ai/jobs/KIS_2-check/codex-task.md` — `api-orders-paper-002-cancel-replace` 의 request.ko.md 초안.
- code / production catalog / `.env` / GUI 어떤 파일도 수정 없음.

## Feature classification re-check (catalog 행 직접 인용)

| 기능 | audit 분류 | catalog 인용 | 재검증 |
| --- | --- | --- | --- |
| `cancel_order` | READY | §4.2 (`/order-rvsecncl` POST, 모의 `VTTT1004U` Confirmed: yes) + §4.6 (CANO/ACNT_PRDT_CD/OVRS_EXCG_CD/PDNO/ORGN_ODNO/`RVSE_CNCL_DVSN_CD="02"`/ORD_QTY/`OVRS_ORD_UNPR="0"` 모두 Confirmed: yes) + §4.5 같은 response 형태 (rt_cd/msg_cd/msg1/output.ODNO Confirmed: yes) | OK — 모든 필수 값이 paper-supported. |
| `replace_order` | READY | cancel 과 같은 endpoint·TR_ID. §4.6 만 차이: `RVSE_CNCL_DVSN_CD="01"`, ORD_QTY=새 수량, OVRS_ORD_UNPR=새 단가. 모두 Confirmed: yes. | OK — TWAP/VWAP 정정 불가 제약은 paper LIMIT-only 정책으로 자동 만족. |
| `get_open_orders` | BLOCKED-BY-DOCS | §4.2 (`inquire-nccs` 모의 미지원) + §4.7 (`inquire-ccnl` 모의 `CCLD_NCCS_DVSN="00"` 만 + `output[]` sub-fields `<TBD>`) + §4.8 (모의 미지원 목록에 `TTTS3018R` 명시) | OK — 두 경로 모두 차단. |
| `get_fills` | PARTIALLY READY → 사실상 BLOCKED | §4.7 request 측 9 필드 Confirmed: yes (paper 제약 포함), response 측 `output[]` sub-fields **`<TBD>`** (§4.7 마지막 문단 명시) | OK — request 만 가능하고 response 매핑 불가는 안전 정책 ("catalog 확인 값만 사용") 하에서 BLOCKED 등가. |
| `get_order_status` | BLOCKED-BY-DOCS | 별도 endpoint 없음. §4.7 paper 가 ODNO 검색 불가 (`ORD_DT`/`ORD_GNO_BRNO`/`ODNO` 모두 `""` 필수). `output[]` sub-fields `<TBD>`. | OK — 단건 lookup 도 status mapping 도 불가능. |

모든 분류가 catalog 본문과 일치. 추가 발견된 paper-supported `Confirmed: yes` 행 중 본 audit 가 누락한 항목 없음.

## Decision soundness

### 권고 옵션 (B — split `api-orders-paper-002-cancel-replace`)

- (A) 통합 vs (B) 분리 비교에서 (B) 선택의 근거 — 두 기능이 endpoint·TR_ID·body 구조를 공유한다는 점은 직접 catalog 인용으로 확인됨 (§4.2 의 `VTTT1004U` 가 cancel/replace 공용, §4.6 의 `RVSE_CNCL_DVSN_CD` 만 다름). 코드 중복 최소화 논거 타당.
- (C) query-only 단독은 3 기능 모두 BLOCKED 라서 사실상 불가 — 결론 합리.
- 후속 job 분리 (`KIS_3-inquire-ccnl-output-fields` 다음에 `api-orders-paper-002-query-only`) 권고도 catalog gap 의존성과 정합.

### 작업 단위가 1 개라는 점

요청은 "다음 작업 추천을 하나로 제시한다" 를 명시했고, audit 는 `api-orders-paper-002-cancel-replace` 1 개를 권고했다. recommendation.md §4 와 plan.md §7 이 일관됨.

### request.ko.md 초안

`codex-task.md` 의 fenced `markdown` 블록이 곧 다음 job 의 request.ko.md 본문. 검토:

- 작업 ID / 작업명 명확.
- 사용할 endpoint / TR_ID / body / response 가 catalog §4.2 / §4.6 행을 그대로 인용.
- "절대 하지 말 것" 이 라이브 / 추측 / `get_open_orders` 등 BLOCKED 기능 구현 / market order / OMS 우회 / external HTTP / secret 노출 / GUI 수정 등 plan.md 의 safety 규약 전부 반복.
- 완료 기준이 dry-run 보존 + paper 가드 + sanitize + history dict + 테스트 + safety grep + patch.md 항목까지 포함.
- 모의 미지원 TR_ID 와 실전 TR_ID 가 명시적으로 금지 목록에 등장 — 추측 방지에 효과적.
- `capabilities()` 의 `cancel` / `replace` 플래그 `False` 유지 권고도 명시되어 GUI 회귀 보호.

## Minor design gaps for the next-job plan (not blockers for this audit)

본 audit 는 catalog 검토만 다루었으므로 어댑터 설계 일부 결정은 다음 job 의 plan 단계로 위임된다. 다음 plan 이 명시적으로 해소해야 할 항목 4 개:

### G1 — `_order_history` 의 OVRS_EXCG_CD 보존

- 현재 `KisOrderResponse` (app/broker/kis.py 의 dataclass) 필드는 `internal_order_id`, `broker_order_id`, `broker`, `status`, `submitted_at`, `symbol`, `side`, `quantity`, `limit_price`, `raw_response_sanitized` 10 개. **`exchange` (OVRS_EXCG_CD) 가 없다.**
- `/order-rvsecncl` body 는 원주문의 `OVRS_EXCG_CD` 가 필수. 다음 plan 은 둘 중 하나로 결정 필요:
  - (a) `KisOrderResponse` 에 `exchange: str = "NASD"` 필드 추가 (작은 도메인 변경; 기존 위치 인자 호출 후방 호환).
  - (b) 어댑터의 `_order_history` value 를 별도 dataclass (`KisOrderHistoryEntry`) 로 만들어 exchange 를 포함.
  - (c) 모든 paper US 주문이 `OVRS_EXCG_CD="NASD"` 라는 사실 (api-orders-paper-001 의 `place_order` 가 default 로 `"NASD"` 사용) 을 invariant 로 두고 lookup 시 동일 default 사용.
  - audit 의 codex-task.md 는 이 결정을 명시하지 않음. 다음 plan 이 §3 또는 §4 에서 (a)/(b)/(c) 중 하나를 선택해 정당화해야 한다.

### G2 — cancel/replace 호출 경로

- OMS (`app/oms/manager.py`) 는 `place(intent)` 만 노출하며 `cancel(broker_order_id)` / `replace(broker_order_id, ...)` 메서드가 없다. KisBroker.cancel_order / replace_order 는 현재 호출자가 없는 상태.
- audit 의 codex-task.md 는 "OMS 또는 신뢰된 호출 경로 (예: 관리자 dashboard) 에서만 진입" 으로 표현했지만 구체 경로를 명시하지 않았다. 다음 plan 이 다음 중 하나로 명시해야 한다:
  - (a) OMS 에 `cancel(broker_order_id)` / `replace(broker_order_id, new_intent)` 메서드 추가 (좁은 protocol 확장).
  - (b) 별도 admin / runtime helper (예: `app/runtime/paper_engine.py` 의 `submit_cancel`) 로 노출.
  - (c) 본 job 은 KisBroker.cancel_order / replace_order 본문만 구현하고 호출 경로는 후속 job 으로 분리.
  - audit 가 (c) 를 implicit 으로 권고한 인상이지만, 다음 plan 은 이 점을 명확히 해야 한다.

### G3 — replace 후 ODNO chain

- KIS 의 `/order-rvsecncl` 응답은 정정 처리 결과의 새 `output.ODNO` 를 반환한다. `_order_history` 가 (old_id → response) 만 유지하는지, (old_id → response) + (new_id → updated_response) 양쪽을 유지하는지, 또는 chain 으로 연결하는지 (`KisOrderResponse.previous_broker_order_id`) 가 결정되지 않았다.
- 본 job 의 범위에서는 단순히 (a) 정정 후 old_id 항목을 제거하고 new_id 로 갱신하는 것이 깔끔. 다음 plan 이 명시 필요.

### G4 — paper Asia 거래소 cancel TR_ID 의 명시적 OOS 선언

- catalog §4.2 는 "그 외 아시아는 정정취소 sheet `tr_id` 셀 본문 참조" 로 명시. audit 는 미국 `VTTT1004U` 만 paper-supported 로 사용한다고 implicit 으로 결정했지만, codex-task.md 의 "절대 하지 말 것" 에 **"미국 외 거래소 cancel/replace 는 본 작업 범위 밖. KIS_2 가 Asia paper TR_ID 를 본 catalog 행에 채워 넣지 않았으므로 추측 금지"** 한 줄을 추가해 명시화하는 것이 안전.

## Safety review

- catalog `<TBD>` 또는 `Confirmed: no` 행을 사용하려는 시도 없음. 모든 인용은 `Confirmed: yes` 행에서만.
- 실 endpoint / TR_ID / payload / header 추측 없음.
- 실 base URL / 실전 TR_ID / 모의 미지원 TR_ID 가 audit 본문에 정보 목적으로만 등장 (금지 목록에 명시).
- 실 secret / 계좌번호 / Bearer 토큰 등장 없음.
- 자동 git commit / push / merge / deploy 수행 없음.
- code / `.env` / `.env.example` / `docs/kis/MISSING_OFFICIAL_VALUES.md` / GUI 무변동.
- Strategy / Agent / LLM 이 broker 직접 호출하는 경로 추가 권고 없음.
- OMS / RiskEngine 경계 약화 권고 없음 (다음 job 이 OMS 확장을 한다면 plan 단계에서 회귀 보호 명시 필요).

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| catalog §4.2 / §4.6 / §4.7 / §4.8 행이 정확히 인용됨 | OK |
| 5 개 기능이 READY / PARTIALLY READY / BLOCKED-BY-DOCS 로 분류됨 | OK |
| READY 기능 (cancel + replace) 의 endpoint / TR_ID / body / response 가 plan 에 그대로 명시됨 | OK |
| BLOCKED 기능 (get_open_orders / get_fills / get_order_status) 의 차단 사유가 catalog 행과 함께 명시됨 | OK |
| 다음 작업 1 개 (`api-orders-paper-002-cancel-replace`) 추천 + 후속 job 분리 권고 | OK |
| codex-task.md 가 다음 job 의 request.ko.md 초안으로 채워짐 | OK |
| 코드 / catalog 본문 / `.env` / GUI 변경 없음 | OK |
| commit / push / merge / deploy 수행 안 됨 | OK |
| 다음 plan 이 해소해야 할 design gap (G1~G4) 명시 | OK |

## Follow-up

- **다음 job 의 plan 작성 시 G1 ~ G4 를 §3 또는 §4 에서 명시적으로 결정할 것.** 특히 G1 (`_order_history` exchange 보존) 과 G2 (호출 경로) 는 어댑터 구조에 직접 영향.
- catalog gap 해소 job (`KIS_3-inquire-ccnl-output-fields`) 은 본 audit 의 권고로만 남기고 별도 request.ko.md 초안은 작성하지 않음 (catalog 본문이 사용자 작업 영역).
- 본 review 자체도 코드 / catalog / `.env` / GUI 어떤 파일도 수정하지 않았다.

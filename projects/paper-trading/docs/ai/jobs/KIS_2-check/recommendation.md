# KIS_2-check — Recommendation Summary

## 1. KIS_2 catalog 요약 (주문 §4)

- paper-supported `Confirmed: yes` endpoint:
  - `/order` POST (`VTTT1002U` BUY / `VTTT1001U` SELL) — **api-orders-paper-001 에서 이미 구현 완료**
  - `/order-rvsecncl` POST (`VTTT1004U` 정정·취소 공용) — 본 audit 의 cancel + replace 후보
  - `/inquire-ccnl` GET (`VTTS3035R`) — request 측 confirmed, **response `output[]` sub-fields `<TBD>`**
  - `/order-resv` / `/order-resv-ccnl` — 예약주문 (본 audit scope 외)
- paper-**미지원**:
  - `/inquire-nccs` (미체결내역)
  - 예약주문조회 / 미국 주간 / 지정가 주문번호·체결내역

## 2. 기능별 결정

| 기능 | 상태 | 핵심 근거 |
| --- | --- | --- |
| `cancel_order` | **READY** | §4.2 + §4.6 모두 `Confirmed: yes`. `/order-rvsecncl` + `VTTT1004U` + body 7 필드 + response 6 필드 paper-confirmed. |
| `replace_order` | **READY** | cancel 과 동일 endpoint·TR_ID·body 구조. `RVSE_CNCL_DVSN_CD="01"` (정정) + 새 `ORD_QTY` / `OVRS_ORD_UNPR` 만 다름. |
| `get_open_orders` | **BLOCKED-BY-DOCS** | (a) `inquire-nccs` 모의 미지원. (b) `inquire-ccnl` paper 에서 `CCLD_NCCS_DVSN="02"` 사용 불가 + `output[]` sub-fields `<TBD>`. |
| `get_fills` | **PARTIALLY READY → 사실상 BLOCKED** | request 측 완전 confirmed. **response `output[]` sub-fields `<TBD>`** → 내부 `Fill` 모델 매핑 불가. |
| `get_order_status` | **BLOCKED-BY-DOCS** | 별도 endpoint 없음. paper 에서 ODNO 검색 불가 (모두 `""` 필수) + `output[]` sub-fields `<TBD>`. |

## 3. 부족한 공식값

| ID | 부족 | 해결 경로 |
| --- | --- | --- |
| C1 | `VTTS3035R` `output[]` sub-fields full list (fill id, symbol, side, qty, price, time, status, remaining qty 등) | `KIS_3-inquire-ccnl-output-fields` (가칭) job — 6.xlsx 주문체결내역 sheet 추가 catalog 화 |
| C2 | `inquire-nccs` paper 지원 또는 `inquire-ccnl` 의 `CCLD_NCCS_DVSN="02"` paper 허용 | KIS 측 정책. C1 이 해소되면 client-side 필터로 우회 가능 |
| C3 | `inquire-ccnl` ODNO 검색 paper 허용 | KIS 측 정책. C1 이 해소되면 client-side 단건 lookup 으로 우회 가능 |

**핵심 차단점은 C1.** C1 이 해소되면 query 3 기능 모두 후속 job 으로 구현 가능.

## 4. 다음 작업 추천 (1 개)

**`api-orders-paper-002-cancel-replace`**

이유:

1. cancel + replace 가 동일 endpoint (`/order-rvsecncl`) + 동일 paper TR_ID (`VTTT1004U`) + 거의 동일한 body 를 공유. 한 job 으로 묶으면 transport / body builder / response parser / `_order_history` state 를 한 번만 작성.
2. query 3 기능 (`get_open_orders` / `get_fills` / `get_order_status`) 은 C1 catalog gap 해소 전까지 BLOCKED. 명확히 분리해 추측 구현 방지.
3. api-orders-paper-001 / api-account-001 / api-market-data-001 의 좁은-scope 패턴과 정합.

후속 job 분리:

- `KIS_3-inquire-ccnl-output-fields` — catalog 보강 (코드 변경 없음).
- `api-orders-paper-002-query-only` — KIS_3 이후 `get_fills` 본문 + (paper 제약 내) `get_open_orders` / `get_order_status` client-side 필터 우회 구현.

## 5. request.ko.md 초안 작성 여부

**작성함** — `docs/ai/jobs/KIS_2-check/codex-task.md` 에 `api-orders-paper-002-cancel-replace` 의 request.ko.md 초안을 작성. 사용자가 검토 후 `docs/ai/jobs/api-orders-paper-002-cancel-replace/request.ko.md` 로 이동하면 다음 turn 에서 Claude 가 plan + codex-task 단계로 진행 가능.

## 6. 작업 후 상태

본 audit 는 **코드 / catalog 본문 / `.env` / GUI 모두 무변동**. 산출물 3 개 파일만 생성:

- `docs/ai/jobs/KIS_2-check/plan.md` (전체 분석)
- `docs/ai/jobs/KIS_2-check/recommendation.md` (본 문서)
- `docs/ai/jobs/KIS_2-check/codex-task.md` (다음 작업 request.ko.md 초안)

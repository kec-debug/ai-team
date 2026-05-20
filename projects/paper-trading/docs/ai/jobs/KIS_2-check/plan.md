# KIS_2-check — KIS_2 catalog 확인 및 `api-orders-paper-002` 작업 가능 여부 판단

본 문서는 **Claude 단독 audit** 결과다. 코드 변경 없음. 본 plan 의 결정은 다음 Codex 작업의 scope 결정에만 사용된다.

## 1. 요청 요약

KIS_2 가 `docs/kis/MISSING_OFFICIAL_VALUES.md` 에 KIS Open API 모의투자 주문 / 정정취소 / 미체결 / 체결 endpoint catalog 를 정리했다. 후속 `api-orders-paper-002` 의 5 개 기능 (`cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status`) 별로 catalog 의 paper-supported `Confirmed: yes` 행이 충분한지 확인하고, READY / PARTIALLY READY / BLOCKED-BY-DOCS 로 분류한 뒤, 다음 작업을 하나로 묶을지 / 분리할지 판단한다.

## 2. 작업 범위

포함:

- `docs/kis/MISSING_OFFICIAL_VALUES.md` §4 (모의투자 주문) 의 모든 `Confirmed: yes` / `Confirmed: no` / `<TBD>` 행 검증.
- 기능별 endpoint / TR_ID / method / headers / request fields / response fields 의 paper-supported 여부 분류.
- 부족한 공식값 (특히 response output[] sub-fields) 의 식별.
- `KisBroker` 의 현재 API 시그니처 (`cancel_order(broker_order_id)` / `replace_order(broker_order_id, broker_order)` / `get_open_orders()` / `get_fills()` / `get_order_status(broker_order_id)`) 가 catalog 필드와 호환되는지 분석.
- 다음 Codex 작업 단위 추천 (`api-orders-paper-002` 통합 / `-cancel-replace` 분리 / `-query-only` 분리).
- 다음 작업이 READY 인 경우 `request.ko.md` 초안을 `codex-task.md` 로 작성.

제외:

- 코드 / 테스트 / catalog 본문 / `.env` / GUI / status surface / Strategy / Agent 변경.
- KIS endpoint / TR_ID / payload / header / response field 추측. catalog 의 `<TBD>` 또는 `Confirmed: no` 행을 채우려는 시도.
- live trading 활성화. 실 broker API 호출. 실 secret / 계좌번호 / token 기록.
- 자동 git commit / push / merge / deploy.

## 3. 수정해야 할 파일

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `projects/paper-trading/docs/ai/jobs/KIS_2-check/plan.md` | NEW | 본 audit 의 전체 분석 + 결정 (본 파일). |
| `projects/paper-trading/docs/ai/jobs/KIS_2-check/recommendation.md` | NEW | 기능별 상태 + 권고 + 다음 작업 단위 요약. |
| `projects/paper-trading/docs/ai/jobs/KIS_2-check/codex-task.md` | NEW | 다음 작업 (`api-orders-paper-002-cancel-replace`) 의 request.ko.md 초안 (Codex 가 다음 turn 에서 그대로 read). |

손대지 않는 파일: `app/` 전체, `tests/` 전체, `docs/kis/MISSING_OFFICIAL_VALUES.md`, `.env`, `.env.example`, GUI 파일, KIS_2 외 다른 job 디렉터리.

## 4. KIS_2 catalog 요약 — 주문 관련 §4

§4.2 endpoint catalog 의 paper-supported 행만 추출:

| 메뉴 | path | method | 모의 TR_ID | Confirmed |
| --- | --- | --- | --- | --- |
| 해외주식 주문 | `/uapi/overseas-stock/v1/trading/order` | POST | `VTTT1002U` (US BUY), `VTTT1001U` (US SELL) | yes |
| 해외주식 **정정취소주문** | `/uapi/overseas-stock/v1/trading/order-rvsecncl` | POST | **`VTTT1004U` (US 정정·취소 공용)** | yes |
| 해외주식 예약주문접수 | `/uapi/overseas-stock/v1/trading/order-resv` | POST | `VTTT3014U` / `VTTT3016U` (US) / `VTTS3013U` (Asia) | yes (※ 본 audit scope 외) |
| 해외주식 예약주문접수취소 | `/uapi/overseas-stock/v1/trading/order-resv-ccnl` | POST | `VTTT3017U` (US 만) | yes (※ scope 외) |
| 해외주식 **주문체결내역** | `/uapi/overseas-stock/v1/trading/inquire-ccnl` | GET | **`VTTS3035R` (모의 제약 §4.7)** | yes — request 필드 yes, output[] sub-fields **`<TBD>`** |

paper-**unsupported** (모의 미지원):

- `inquire-nccs` (미체결내역) — `TTTS3018R` 실전만.
- `order-resv-list` (예약주문조회) — 실전만.
- `daytime-order` / `daytime-order-rvsecncl` — 실전만.
- `algo-ordno` / `inquire-algo-ccnl` (지정가 주문번호 / 체결내역 조회) — 실전만.

§4.3 (헤더) 와 §4.4 (`/order` body) 는 이미 api-orders-paper-001 에서 소비됐고 본 audit 와는 무관.

§4.6 정정취소 body 필드 (`Confirmed: yes` 모두):

- `CANO`, `ACNT_PRDT_CD`, `OVRS_EXCG_CD`, `PDNO` — 계좌 / 거래소 / 종목 (필수)
- `ORGN_ODNO` — 원주문번호 (필수). 출처: `/order` 응답의 `output.ODNO` 또는 미체결 조회의 `odno`.
- `RVSE_CNCL_DVSN_CD` — `01`=정정, `02`=취소 (필수)
- `ORD_QTY` — 주문수량 (필수)
- `OVRS_ORD_UNPR` — 단가 (필수, 취소 시 `"0"`)
- `MGCO_APTM_ODNO` / `ORD_SVR_DVSN_CD` — 옵션

정정취소 Response body 핵심 필드 (`/order` 와 동일): `rt_cd`, `msg_cd`, `msg1`, `output.KRX_FWDG_ORD_ORGNO`, `output.ODNO`, `output.ORD_TMD`. **모두 `Confirmed: yes`**.

§4.7 주문체결내역 (`VTTS3035R`) request query — **모든 필드 `Confirmed: yes` (모의 제약 별도 명시)**:

- `CANO`, `ACNT_PRDT_CD` — 계좌 (필수)
- `PDNO` — 종목코드 (필수). **모의는 `""` (전체) 만**.
- `ORD_STRT_DT`, `ORD_END_DT` — 주문 기간 (필수, YYYYMMDD 현지시각)
- `SLL_BUY_DVSN` — `00`=전체 / `01`=매도 / `02`=매수 (필수). **모의는 `"00"` 만**.
- `CCLD_NCCS_DVSN` — `00`=전체 / `01`=체결 / `02`=미체결 (필수). **모의는 `"00"` 만**.
- `OVRS_EXCG_CD` — 거래소 (필수, 모의는 `NASD`/`NYSE`/`AMEX` 또는 `%` 전체 — §4.4 거래소 제약 따름)
- `SORT_SQN` — `DS`=정순 / `AS`=역순 (필수). **모의는 정렬 옵션 사용 불가 (Default `DS`)**.
- `ORD_DT`, `ORD_GNO_BRNO`, `ODNO` — Null (필수). **모의는 주문번호 검색 불가, 반드시 `""`**.
- `CTX_AREA_NK200`, `CTX_AREA_FK200` — 연속조회 키 (필수)

§4.7 Response body — `rt_cd`, `msg_cd`, `msg1`, `output[]` array. **`output[]` 의 sub-field full list 는 본 catalog 가 보유하지 않음 (`<TBD>`)**. 매핑 단계에서 6.xlsx 주문체결내역 sheet 의 sub-field 표를 추가 catalog 화 필요.

§4.10 안전 정책 재확인 (전체 적용):

- 모든 주문은 Strategy → RiskEngine → OMS → Broker 경로.
- `KIS_ORDER_DRY_RUN=true` 기본 + `validate_kis_order_request` preflight + `ALLOW_MARKET_ORDERS=true` reject 유지.
- LLM/Agent 는 non-executable `OrderIntent` 까지만. executable `BrokerOrder` / `Order` 생성은 OMS 만.
- secret / 계좌번호 / token 원문 코드/문서/응답/로그 기록 금지.

## 5. 기능별 분석

### 5.1 `cancel_order()` — **READY**

| 항목 | 값 | 출처 | Status |
| --- | --- | --- | --- |
| 모의 endpoint | `/uapi/overseas-stock/v1/trading/order-rvsecncl` | §4.2 | Confirmed: yes |
| 모의 TR_ID | `VTTT1004U` (US 정정·취소 공용) | §4.2 | Confirmed: yes |
| HTTP method | POST | §4.2 | Confirmed: yes |
| Headers | content-type / authorization (Bearer) / appkey / appsecret / tr_id (+ 옵션) | §4.3 = §2.3 | Confirmed: yes |
| Required body — 계좌 / 거래소 / 종목 | `CANO` / `ACNT_PRDT_CD` / `OVRS_EXCG_CD` / `PDNO` | §4.6 | Confirmed: yes |
| Required body — 원주문번호 | `ORGN_ODNO` | §4.6 | Confirmed: yes |
| Required body — 정정/취소 구분 | `RVSE_CNCL_DVSN_CD="02"` (취소) | §4.6 | Confirmed: yes |
| Required body — 수량 | `ORD_QTY` (원주문 수량) | §4.6 | Confirmed: yes |
| Required body — 단가 | `OVRS_ORD_UNPR="0"` (취소 시 명시 규칙) | §4.6 | Confirmed: yes |
| Response 성공 / 실패 | `rt_cd` ("0"=성공) | §4.6 (=§4.5) | Confirmed: yes |
| Response 에러 코드 / 메시지 | `msg_cd` / `msg1` | §4.6 | Confirmed: yes |
| Response 응답 주문번호 | `output.ODNO` (취소 처리 결과의 주문번호) | §4.6 | Confirmed: yes |

**결론: 구현 가능.** Catalog 가 cancel 에 필요한 모든 값을 paper-supported 로 보장한다.

**구현 시 주의 (catalog gap 아님, 어댑터 설계 사안)**:

- 현재 `KisBroker.cancel_order(broker_order_id: str)` 시그니처는 `broker_order_id` 만 받는다. KIS 의 `/order-rvsecncl` 는 `PDNO` / `ORD_QTY` 도 필요. → 어댑터 내부에서 `(broker_order_id → (symbol, quantity))` 매핑을 보관해야 한다. api-orders-paper-001 이 이미 `_last_order_response: KisOrderResponse | None` 단일 슬롯에 마지막 주문 응답을 저장한다. 이를 **dict 형 history (`_order_history: dict[str, KisOrderResponse]`) 로 확장**하면 (symbol, quantity, ORD_QTY = quantity, OVRS_ORD_UNPR="0") 조회 가능.
- OMS / domain 계약은 그대로 유지. `broker.cancel_order(broker_order_id)` 가 history 에서 ORGN_ODNO 를 lookup 하지 못하면 `KisOrderRejectedError("unknown_broker_order_id")` 로 fail-closed.

### 5.2 `replace_order()` — **READY**

| 항목 | 값 | 출처 | Status |
| --- | --- | --- | --- |
| 모의 endpoint | `/uapi/overseas-stock/v1/trading/order-rvsecncl` (cancel 과 공용) | §4.2 | Confirmed: yes |
| 모의 TR_ID | `VTTT1004U` (cancel 과 공용) | §4.2 | Confirmed: yes |
| HTTP method | POST | §4.2 | Confirmed: yes |
| Headers | (cancel 과 동일) | §4.3 | Confirmed: yes |
| Required body — 계좌 / 거래소 / 종목 | `CANO` / `ACNT_PRDT_CD` / `OVRS_EXCG_CD` / `PDNO` | §4.6 | Confirmed: yes |
| Required body — 원주문번호 | `ORGN_ODNO` | §4.6 | Confirmed: yes |
| Required body — 정정/취소 구분 | `RVSE_CNCL_DVSN_CD="01"` (정정) | §4.6 | Confirmed: yes |
| Required body — 새 수량 | `ORD_QTY` (정정 후 수량) | §4.6 | Confirmed: yes |
| Required body — 새 단가 | `OVRS_ORD_UNPR` (정정 단가) | §4.6 | Confirmed: yes |
| Response 성공/실패 + 새 주문번호 + 시각 | `rt_cd` / `output.ODNO` / `output.ORD_TMD` | §4.6 | Confirmed: yes |

**결론: 구현 가능.** Catalog 가 정정에 필요한 모든 값을 paper-supported 로 보장한다.

**구현 시 주의**:

- `KisBroker.replace_order(broker_order_id, new_broker_order)` 시그니처는 그대로. 새 `BrokerOrder` 가 새 quantity / limit_price 를 운반. 어댑터는 `_order_history` 에서 원주문의 (symbol, ORGN_ODNO) 를 lookup. 새 주문이 LIMIT 외 또는 paper 미허용 거래소면 거절.
- 모의는 LIMIT 만 (`ORD_DVSN="00"`). 정정도 동일 제약. `validate_kis_order_request` 가 이미 강제하므로 추가 가드 불필요.

### 5.3 `get_open_orders()` — **BLOCKED-BY-DOCS**

| 항목 | 값 | 출처 | Status |
| --- | --- | --- | --- |
| Native 미체결 endpoint | `/uapi/overseas-stock/v1/trading/inquire-nccs` | §4.2 | **모의 미지원** ✗ |
| Native 미체결 TR_ID | `TTTS3018R` 실전 only | §4.2, §4.8 | **모의 미지원** ✗ |
| 대체 경로 1 | `/inquire-ccnl` (VTTS3035R) 의 `CCLD_NCCS_DVSN="02"` (미체결) | §4.7 | **모의는 `CCLD_NCCS_DVSN="00"` 만** → 필터링 불가 ✗ |
| 대체 경로 2 | `/inquire-ccnl` 전체 호출 후 응답에서 미체결만 client-side 필터 | §4.7 | `output[]` sub-field full list **`<TBD>`** → 상태 필드 식별 불가 ✗ |

**결론: 구현 불가.** 두 가지 차단 사유가 동시 발생:

1. paper-native 미체결 endpoint (`inquire-nccs`) 가 모의 미지원으로 catalog 에 명시.
2. 유일한 paper-supported 조회 endpoint (`inquire-ccnl`) 는 모의에서 (a) `CCLD_NCCS_DVSN="02"` 미체결 필터 사용 불가 (`"00"` 전체만), (b) 응답 `output[]` 의 sub-field 가 `<TBD>` 라서 status / 잔여수량 컬럼명을 catalog 에서 확인 불가.

**부족한 공식값**:

- `inquire-nccs` 의 모의 지원 여부 변경 (KIS 측 정책 변경 필요 — 본 저장소가 해결할 수 없음).
- 또는 `inquire-ccnl` 의 `CCLD_NCCS_DVSN="02"` 모의 허용 (KIS 측 정책 변경 필요).
- 또는 `inquire-ccnl` 의 `output[]` sub-field full list 가 catalog `<TBD>` 에서 채워져야 함 (특히 미체결 / 부분체결 상태를 식별할 수 있는 status / 수량 / 잔여수량 컬럼) — 별 job `KIS_3-inquire-ccnl-output-fields` 가 필요.

설령 `output[]` sub-fields 가 채워져도, **paper 가 `CCLD_NCCS_DVSN="00"` 만 허용** 하므로 client-side 필터링이 불가피하다. 본 어댑터의 안전 원칙 ("catalog 확인된 값만 사용") 하에서, "어떤 sub-field 가 status 를 나타내는지" 가 KIS 공식 catalog 로 confirmed 되어야 필터링 가능. 따라서 본 기능은 **2-단계 차단** 상태.

### 5.4 `get_fills()` — **PARTIALLY READY → 사실상 BLOCKED-BY-DOCS**

| 항목 | 값 | 출처 | Status |
| --- | --- | --- | --- |
| 모의 endpoint | `/uapi/overseas-stock/v1/trading/inquire-ccnl` | §4.2 | Confirmed: yes |
| 모의 TR_ID | `VTTS3035R` | §4.2 | Confirmed: yes |
| HTTP method | GET | §4.2 | Confirmed: yes |
| Headers | (cancel 과 동일) | §4.3 | Confirmed: yes |
| Required query — 계좌 | `CANO`, `ACNT_PRDT_CD` | §4.7 | Confirmed: yes |
| Required query — 종목 | `PDNO` (모의는 `""` 만) | §4.7 | Confirmed: yes (제약 포함) |
| Required query — 기간 | `ORD_STRT_DT`, `ORD_END_DT` (YYYYMMDD 현지시각) | §4.7 | Confirmed: yes |
| Required query — 매수/매도 | `SLL_BUY_DVSN` (모의는 `"00"` 만) | §4.7 | Confirmed: yes (제약 포함) |
| Required query — 체결/미체결 | `CCLD_NCCS_DVSN` (모의는 `"00"` 만) | §4.7 | Confirmed: yes (제약 포함) |
| Required query — 거래소 | `OVRS_EXCG_CD` | §4.7 | Confirmed: yes |
| Required query — 정렬 | `SORT_SQN` (모의는 옵션 불가, Default `DS`) | §4.7 | Confirmed: yes (제약 포함) |
| Required query — 주문번호 검색 | `ORD_DT` / `ORD_GNO_BRNO` / `ODNO` 모두 `""` | §4.7 | Confirmed: yes (제약 포함) |
| Required query — 페이지네이션 | `CTX_AREA_FK200` / `CTX_AREA_NK200` | §4.7 | Confirmed: yes |
| Response 성공/실패 / 메시지 | `rt_cd` / `msg_cd` / `msg1` | §4.7 | Confirmed: yes |
| Response — 체결/미체결 array | `output[]` | §4.7 | Confirmed: yes (배열 존재) |
| Response — array sub-fields (fill id, symbol, side, qty, price, time 등) | **`<TBD>`** | §4.7 | **Confirmed: no** ✗ |

**결론: request 측은 완전 confirmed, response 측은 sub-field full list 미확인.** 본 어댑터의 안전 원칙 ("catalog 의 `Confirmed: yes` 필드만 사용") 하에서, `output[]` 의 sub-field 가 `<TBD>` 인 동안에는:

- `Fill` / `OrderAck` 같은 내부 모델로 변환할 수 없음 (필드 매핑 불가).
- raw sanitized list 만 노출 가능하지만 그러면 OMS / Journal 와의 도메인 통합 불가.
- 가장 안전한 처리: 호출 자체는 가능하지만 결과를 **fail-closed** (`KisOrderRejectedError("paper_inquire_ccnl_output_subfields_unconfirmed")`) — 현재 NotImplementedError 와 본질적으로 동일 상태.

따라서 기능적 가치 0. 본 audit 는 **사실상 BLOCKED-BY-DOCS** 로 분류한다.

**부족한 공식값**:

- `VTTS3035R` 응답의 `output[].*` sub-field full list. 최소 필요:
  - `output[]` 의 fill 식별 ID (체결번호 또는 주문번호)
  - 종목 (PDNO / OVRS_PDNO 등)
  - 매수/매도 구분 (SLL_BUY_DVSN 또는 동등 필드)
  - 체결 수량 / 주문 수량 / 잔여 수량
  - 체결 단가 / 주문 단가
  - 체결 시각 / 주문 시각
  - 상태 (체결 / 미체결 / 부분체결 / 거절 등)

이 sub-field 는 사용자의 KIS_2 catalog 작업 마지막 단계에서 `<TBD>` 로 남긴 항목이며, **`KIS_3-inquire-ccnl-output-fields` (가칭) job 에서 6.xlsx 주문체결내역 sheet 의 sub-field 표를 추가로 catalog 화** 해야 한다.

### 5.5 `get_order_status()` — **BLOCKED-BY-DOCS**

| 항목 | 값 | 출처 | Status |
| --- | --- | --- | --- |
| 별도 endpoint 존재 여부 | **없음**. KIS 의 "주문상태 조회" 는 `inquire-nccs` + `inquire-ccnl` 조합으로 표현됨. | §4.2 | — |
| ODNO 기준 단건 조회 가능 여부 | `inquire-nccs` 는 모의 미지원. `inquire-ccnl` 은 모의에서 `ODNO` 검색 불가 (모두 `""` 필수). | §4.7, §4.8 | **불가** ✗ |
| Response status mapping 가능 여부 | `inquire-ccnl` `output[]` sub-fields `<TBD>` → 상태 필드 식별 불가. | §4.7 | **불가** ✗ |

**결론: 구현 불가.** Paper 에서는 `(broker_order_id) → 상태` 매핑이 catalog 만으로 작동 불가능. 우회 경로 (전체 fetch + client filter) 도 5.3 / 5.4 와 동일하게 `output[]` sub-fields `<TBD>` 에 의해 차단.

**부족한 공식값** (5.3 / 5.4 의 합집합):

- `inquire-nccs` 모의 지원 (KIS 정책).
- 또는 `inquire-ccnl` 의 ODNO 검색 모의 허용 (KIS 정책).
- 그리고 `inquire-ccnl` `output[].*` sub-fields full list (catalog `<TBD>` 해소).

## 6. 부족한 공식값 목록 (정리)

| 차단 사유 | 부족한 값 | 해결 경로 |
| --- | --- | --- |
| C1 | `inquire-ccnl` (`VTTS3035R`) Response `output[]` sub-fields full list (fill id, symbol, side, qty, price, time, status, remaining qty 등) | 사용자가 6.xlsx 주문체결내역 sheet 의 sub-field 표를 catalog 화 → `KIS_3-inquire-ccnl-output-fields` 가칭 job |
| C2 | `inquire-nccs` 의 paper 지원 활성화 또는 `inquire-ccnl` 의 `CCLD_NCCS_DVSN="02"` paper 허용 | KIS 측 정책 (본 저장소가 해결 불가). 또는 C1 해소 후 client-side 필터로 우회 가능 |
| C3 | `inquire-ccnl` 의 `ODNO` 검색 paper 허용 | KIS 측 정책. 또는 C1 해소 후 client-side 단건 lookup 으로 우회 가능 |

**핵심 차단점은 C1 (output[] sub-fields).** C1 이 해소되면:

- `get_fills()` 는 paper-supported 조회로 완전 구현 가능 (전체 fetch + sub-field 매핑).
- `get_open_orders()` 와 `get_order_status()` 는 client-side 필터로 우회 구현 가능 (paper 가 status sub-field 를 응답에 포함하는 한).

## 7. 다음 작업 추천

### 7.1 옵션 비교

| 옵션 | scope | 장점 | 단점 |
| --- | --- | --- | --- |
| (A) `api-orders-paper-002` 통합 | 5 개 기능 모두 한 job 으로 | 한 PR 로 마무리 | 5 개 중 3 개가 BLOCKED → 실제로 구현되는 것은 cancel / replace 만. job 명세와 실제 구현 분량 불일치 |
| (B) `api-orders-paper-002-cancel-replace` 분리 (**권고**) | cancel + replace 만 | (a) 두 기능이 정확히 같은 endpoint·TR_ID 공유 → 코드 중복 최소. (b) 상태 dict (`_order_history`) 도입을 한 번에 끝낼 수 있음. (c) 다른 3 기능은 catalog 가 차단된 상태 그대로 명확하게 보고 | 후속 job 이 2-3 개 (KIS_3 → query-only) 로 늘어남 |
| (C) `api-orders-paper-002-query-only` 단독 | get_open_orders + get_fills + get_order_status | — | 3 개 모두 BLOCKED → 구현 불가. 권고 불가 |

### 7.2 권고: **옵션 B — `api-orders-paper-002-cancel-replace`**

근거:

1. cancel / replace 는 동일 endpoint (`/order-rvsecncl`) + 동일 TR_ID (`VTTT1004U`) + 동일 body 구조 (`RVSE_CNCL_DVSN_CD` 만 다름) 를 공유한다. 한 job 에서 함께 구현하면 transport / body builder / response parser / `_order_history` state 를 한 번만 작성하면 된다.
2. query 3 기능 (`get_open_orders` / `get_fills` / `get_order_status`) 은 `output[]` sub-fields catalog 가 채워지기 전까지 모두 BLOCKED. 본 audit 의 결정을 명확히 후속 job 분리로 반영해 BLOCKED 기능의 추측 구현을 방지한다.
3. api-orders-paper-001 / api-account-001 / api-market-data-001 가 같은 패턴 (좁은 scope, paper-supported confirmed 값만 사용, transport 별 정의) 으로 안정적이었다. cancel-replace 분리도 이 패턴에 맞다.

### 7.3 따로 진행할 후속 job

- **`KIS_3-inquire-ccnl-output-fields`**: 사용자의 6.xlsx 주문체결내역 sheet 의 sub-field 표를 `docs/kis/MISSING_OFFICIAL_VALUES.md` §4.7 의 `output[]` `<TBD>` 자리에 추가 catalog 화. 코드 변경 없음.
- **`api-orders-paper-002-query-only`** (KIS_3 이후 가능): `output[]` sub-fields 가 confirmed 된 뒤 `get_fills()` 본문 + (paper 제약 내) `get_open_orders()` / `get_order_status()` 의 client-side 필터 우회 구현.

본 audit 는 KIS_3 / query-only job 의 request.ko.md 초안을 작성하지 않는다 (catalog 가 아직 차단됨).

## 8. 다음 작업 codex-task.md (`api-orders-paper-002-cancel-replace`) 초안

본 plan 의 §7 권고에 따라 `docs/ai/jobs/KIS_2-check/codex-task.md` 에 다음 작업의 **request.ko.md 초안** 을 작성한다. 해당 파일은 사용자가 검토 후 `docs/ai/jobs/api-orders-paper-002-cancel-replace/request.ko.md` 로 이동하면 Codex 가 plan/codex-task 단계로 진행할 수 있다.

초안에는 다음 항목 포함:

- 작업 ID / 작업명
- 목표: cancel_order + replace_order 본문 구현 (catalog §4.6 `Confirmed: yes` 필드만 사용)
- 확인할 endpoint·TR_ID·body·response 필드 (본 plan §5.1 + §5.2 의 값 그대로)
- 절대 하지 말 것 (live trading / 실전 TR_ID / get_open_orders·get_fills·get_order_status 본문 구현 / market order / `.env` / secret 등)
- 완료 기준 (dry-run 보존 / paper 가드 / sanitize / `_order_history` 도입 / 테스트 / 안전 grep)
- patch.md 요구 항목

## 9. 리뷰 체크리스트 (본 audit 의 self-check)

- [x] §4.2 endpoint catalog 모든 행 검토.
- [x] §4.6 정정취소 body 필드 모든 행 `Confirmed: yes` 확인.
- [x] §4.7 주문체결내역 request 필드 모든 행 `Confirmed: yes` 확인.
- [x] §4.7 response `output[]` sub-fields 가 `<TBD>` 임을 명시.
- [x] §4.8 모의 미지원 endpoint 목록과 5.3 / 5.4 / 5.5 분류 일치.
- [x] 각 기능 (5.1 ~ 5.5) 이 READY / PARTIALLY READY / BLOCKED-BY-DOCS 중 하나로 명확히 분류됨.
- [x] READY 기능 (cancel / replace) 에 필요한 endpoint / TR_ID / body / response 필드가 plan 에 그대로 인용됨.
- [x] BLOCKED 기능 (open_orders / fills / order_status) 의 차단 사유가 catalog 행과 함께 명시됨.
- [x] 다음 작업 단위 1 개 추천 (`api-orders-paper-002-cancel-replace`).
- [x] KIS_3 / query-only 후속 job 분리 권고.
- [x] codex-task.md 가 next-job request.ko.md 초안으로 채워짐 (별도 파일).
- [x] 코드 / catalog 본문 / `.env` 변경 없음.
- [x] commit / push / merge / deploy 수행 없음.

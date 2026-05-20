# roadmap-implementation-plan — next-job seed (api-orders-paper-003-query)

본 파일은 master plan §8 의 권고 결과로 작성된 **다음 단일 Codex job 의 request.ko.md 초안**이다. 본 turn 의 Codex 가 실행할 작업은 아니다 — 사용자가 (a) master plan §8 의 Phase 0 (commit dirty) 를 먼저 수행한 뒤, (b) 본 fenced 블록을 그대로 `projects/paper-trading/docs/ai/jobs/api-orders-paper-003-query/request.ko.md` 로 옮기고, (c) GUI 한국어 작업 요청 칸에 입력해 Claude plan + codex-task 단계로 진입하면 된다.

본 초안은 KIS_3 의 `docs/ai/jobs/KIS_3/next-job-request.md` 와 본질적으로 동일하지만 master plan §8 의 risk note + alternative 가 반영된 self-contained 버전이다.

---

```markdown
# 작업 ID
api-orders-paper-003-query

# 작업명
KIS 모의투자 미체결 / 체결 / 주문상태 조회 구현 (adapter-level partial query)

KIS_3 (`docs/kis/MISSING_OFFICIAL_VALUES.md` §4.7.1) 에서 `VTTS3035R` 주문체결내역 response `output[]` sub-field 이름이 catalog 화되었다. 본 작업은 `KisBroker.get_open_orders()` / `get_fills()` / `get_order_status()` 를 catalog §4.7 + §4.7.1 의 paper-supported `Confirmed: yes` 필드만 사용해 adapter-level 부분 구현한다.

세 메서드 모두 paper 제약 때문에 **PARTIALLY READY** 다 (KIS_2-check audit + KIS_3 recommendation 참조):

- `get_open_orders`: native `/inquire-nccs` (`TTTS3018R`) 모의 미지원. `/inquire-ccnl` 전체 조회 후 `nccs_qty > 0` / `prcs_stat_name` 기반 client-side filtering 만 허용.
- `get_fills`: 별도 fill id / 명확한 체결시각 field 없음. `odno` + `ft_ccld_qty` / `ft_ccld_unpr3` / `ft_ccld_amt3` / `ord_tmd` 기반 projection 또는 sanitized broker row 반환으로 제한.
- `get_order_status`: 별도 주문상태 endpoint 및 paper ODNO query 없음. 전체 조회 후 client-side ODNO lookup 만 허용. 조회 범위 밖이면 fail-closed.

이번 작업은 실전 주문이 아니라 paper trading 의 주문 상태 추적 / reconciliation 을 위한 read-only 조회 구현이다.

## 목표

- `KisBroker.get_open_orders()` 본문을 catalog §4.7 + §4.7.1 의 `Confirmed: yes` 필드만 사용해 구현한다.
- `KisBroker.get_fills()` 본문을 동일 catalog 행만 사용해 구현한다.
- `KisBroker.get_order_status(broker_order_id)` 본문을 동일 catalog 행 + client-side ODNO lookup 으로 구현한다.
- 세 메서드 모두 adapter-level only. OMS protocol 확장 없음.
- GUI / status surface / capabilities 공개 변경 없음. `capabilities()["open_orders"]`, `["fills"]`, `["order_status"]` 는 별도 status-surface job 전까지 `False` 유지.
- query 는 GET 이므로 새 `KisQueryTransport` Protocol + `UrllibQueryTransport` + `MockQueryTransport` 를 `KisAccountTransport` 패턴 그대로 재사용한다. 기존 `KisOrderTransport` (POST 전용) 는 재사용 금지.
- raw response 는 항상 `sanitize_kis_response` 통과 후 보존.
- 테스트를 추가한다.

## 사용할 catalog 값

사용 가능 (catalog §4.7 + §4.7.1):

- Endpoint: GET `/uapi/overseas-stock/v1/trading/inquire-ccnl`
- Paper TR_ID: `VTTS3035R`
- Method: GET
- Request fields: §4.7 의 `CANO`, `ACNT_PRDT_CD`, `PDNO`, `ORD_STRT_DT`, `ORD_END_DT`, `SLL_BUY_DVSN`, `CCLD_NCCS_DVSN`, `OVRS_EXCG_CD`, `SORT_SQN`, `ORD_DT`, `ORD_GNO_BRNO`, `ODNO`, `CTX_AREA_NK200`, `CTX_AREA_FK200`
- Paper constraints (§4.7): `PDNO=""`, `SLL_BUY_DVSN="00"`, `CCLD_NCCS_DVSN="00"`, `SORT_SQN` default `DS`, `ORD_DT=""`, `ORD_GNO_BRNO=""`, `ODNO=""`
- Response top-level fields: `rt_cd`, `msg_cd`, `msg1`, `ctx_area_fk200`, `ctx_area_nk200`, `output[]`
- Response `output[]` fields from §4.7.1 only — 핵심: `ord_dt`, `odno`, `orgn_odno`, `sll_buy_dvsn_cd`, `pdno`, `ft_ord_qty`, `ft_ord_unpr3`, `ft_ccld_qty`, `ft_ccld_unpr3`, `ft_ccld_amt3`, `nccs_qty`, `prcs_stat_name`, `rjct_rson`, `rjct_rson_name`, `ord_tmd`, `ovrs_excg_cd`, `tr_crcy_cd`

사용 금지:

- `/inquire-nccs` (`TTTS3018R`) in paper. §4.8 에 따라 모의 미지원.
- Live TR_IDs (`TTTS3035R` 실전).
- Paper-unsupported TR_IDs.
- Asia paper query TR_ID 추측.
- §4.7.1 / §4.7.2 에 없는 response field 추측.
- §4.7.2 의 미체결내역 (`TTTS3018R`) sub-fields — 본 catalog 에 있지만 paper 미지원으로 명시되어 있으므로 사용 금지.

## 절대 하지 말 것

- live trading 활성화 / 실전 endpoint / 실전 TR_ID 사용 금지.
- KIS endpoint, TR ID, payload, header, response field 추측 금지.
- `/inquire-nccs` 를 paper query 에 사용 금지.
- `CCLD_NCCS_DVSN="01"` 또는 `"02"` 를 paper query 에 사용 금지. paper 는 반드시 `"00"`.
- `ODNO` query parameter 로 단건 검색 시도 금지. paper 는 반드시 `""` — 단건 lookup 은 client-side filter 로만.
- 외부 HTTP 라이브러리 사용 금지. stdlib `urllib.request` 만 허용.
- `requests`, `httpx`, `aiohttp`, `urllib3`, `openpyxl`, `pandas` 추가 금지.
- OMS protocol 확장 금지. `OMS.fills()` / `OMS.open_orders()` 등 메서드 추가 금지.
- GUI / API / status surface 변경 금지. `app/api/*`, `app/static/*`, `app/main.py` 무변동.
- `capabilities()` 공개 surface 변경 금지. cancel/replace/place/open_orders/fills/order_status 모두 `False` 유지.
- `healthcheck()["order_execution_implemented"]` / `order_methods_fail_closed` 변경 금지.
- Strategy, Agent, LLM 이 broker 를 직접 호출하는 경로 추가 금지.
- OMS / RiskEngine 우회 금지.
- `OrderType.MARKET` 3중 가드 우회 금지.
- `ALLOW_MARKET_ORDERS=true` 허용 금지.
- `OrderType.STOP` 도입 금지.
- FX 변환 함수 / 환율 상수 도입 금지.
- `.env` / `.env.example` 읽기 / 수정 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호 기록 금지.
- payment, auth settings, production infra, database migrations 변경 금지.
- 자동 git commit / push / merge / PR / production deploy 금지.

## 구현 지침

- `app/broker/kis.py` 내부에 GET 전용 query transport 를 추가한다 (`KisAccountTransport` / `UrllibAccountTransport` 패턴 그대로).
- query transport allowlist:
  - paper host only: `openapivts.koreainvestment.com:29443`
  - path only: `/uapi/overseas-stock/v1/trading/inquire-ccnl`
  - method only: GET
  - TR_ID only: `VTTS3035R`
  - exchange: paper-supported US set (`NASD`, `NYSE`, `AMEX`). **`%` (전체) 는 catalog 가 paper 허용 여부를 명시하지 않으므로 fail-closed — US 거래소만 허용.**
  - paper constraints exactly as §4.7 (위 "사용할 catalog 값" 참고).
- Pagination: `ctx_area_fk200` / `ctx_area_nk200` + 페이지 cap (`KIS_QUERY_MAX_PAGES = 10` 권고).
- 매 페이지 응답은 `sanitize_kis_response` 통과 후 누적.
- Missing `rt_cd` → `KisOrderRejectedError("malformed_response")` (또는 적절한 query 전용 exception class — plan 단계에서 결정).
- `rt_cd != "0"` → `KisOrderRejectedError(f"kis_error:{msg_cd}")`.
- `get_open_orders`: 전체 조회 후 `output[]` 에서 `nccs_qty > 0` 또는 `prcs_stat_name` 이 "체결" / "완료" / "거부" 가 아닌 행만 반환.
- `get_fills`: 전체 조회 후 `output[]` 에서 `ft_ccld_qty > 0` 인 행만 반환. 내부 `Fill` 모델 또는 동등 모델로 매핑.
- `get_order_status(broker_order_id)`: 전체 조회 후 `odno == broker_order_id` 행을 lookup. 없으면 `KisOrderRejectedError("unknown_broker_order_id")` 로 fail-closed (api-orders-paper-002-cancel-replace 의 `_order_history` lookup 패턴과 정합).
- 조회 날짜 범위는 보수적 default (예: 최근 1 일) + caller override 허용. plan 단계에서 결정.
- secret / access_token / app_key / app_secret 은 header 로만 전송. exception message 에 절대 포함 금지.

## 완료 기준

- `get_open_orders()` / `get_fills()` / `get_order_status()` 모두 `VTTS3035R` 전체 조회 + client-side filter / projection / lookup 으로 구현.
- 모든 fail 경로가 `KisOrderRejectedError` (또는 새 query 전용 class) 의 short tag 로 fail-closed.
- `/inquire-nccs` paper 호출 코드 0 건.
- `capabilities()` 플래그 모두 `False` 유지.
- `healthcheck()["order_execution_implemented"]` 와 `order_methods_fail_closed` 변경 없음.
- 테스트 커버리지:
  - happy path × 3 (get_open_orders / get_fills / get_order_status).
  - empty result (output[] 빈 array) × 3.
  - 페이지네이션 (2 페이지 이상).
  - 페이지 cap 초과 fail-closed.
  - paper 제약 (CCLD_NCCS_DVSN="01" 시도 거절 / ODNO non-empty 시도 거절 / `%` 거래소 거절).
  - KIS rt_cd != "0" 전파.
  - malformed response (rt_cd missing) fail-closed.
  - mock-mode fail-closed.
  - auth 미존재 fail-closed.
  - secret leak 회귀 (repr / exception message / sanitized dict).
  - module surface 회귀 (live TR_ID / `/inquire-nccs` paper 호출 / 외부 HTTP lib 부재).
  - Strategy / Agent KIS direct import 부재 회귀.
- 좁은 갱신 후보 (필요시):
  - `tests/test_broker_interface.py::test_kis_data_methods_not_implemented` — `get_open_orders` / `get_fills` / `get_order_status` 가 NotImplementedError 였던 단언을 적절히 갱신.
  - `tests/test_kis_http_boundaries.py::test_cancel_replace_queries_fail_closed` — `get_open_orders` / `get_fills` / `get_order_status` 의 NotImplementedError 단언 갱신.
  - **위 두 함수의 cancel/replace 단언은 절대 변경하지 않는다 — api-orders-paper-002-cancel-replace 에서 이미 갱신됨.**
- 전체 pytest 회귀 0 건.
- 안전 grep clean — 외부 HTTP / 실전 TR_ID / 모의 미지원 TR_ID / live base URL / Strategy·Agent KIS import 모두 0 lines (단 `app/config.py` 의 기존 가드 라인 잔존 가능).
- `patch.md` 에 다음 포함:
  - 수정 파일 목록
  - 사용한 catalog 행 (§4.7 / §4.7.1) 인용
  - 부분 구현 한계 (paper 제약 / catalog gap) 명시
  - dry-run 미적용 사유 (query 는 read-only 이므로 dry-run 개념 부재 — 모든 호출이 실제 GET. 단 mock-mode 는 fail-closed 유지)
  - fail-closed로 남긴 항목 (`/inquire-nccs` paper, paper-unsupported TR_IDs)
  - secret/account/token 노출 없음 확인
  - live trading 비활성 유지 확인
  - market order guard 유지 확인
  - 테스트 결과
  - 안전 grep 결과
  - Claude 검증 요청 프롬프트
  - Claude 리뷰가 REQUEST CHANGES/BLOCK일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙

## 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

전체 PASS 가 완료 조건.
```

---

## 본 master plan 의 비고

- 본 `codex-task.md` 는 master plan §8 의 권고 결과로 작성된 **api-orders-paper-003-query 의 request.ko.md seed** 다.
- 본 turn 의 Codex 가 직접 실행할 작업은 없다. 사용자가 master plan §8 의 Phase 0 (commit dirty) 를 먼저 수행하고, 이 fenced 블록을 새 job 디렉터리로 옮긴 뒤, GUI 에서 plan + codex-task 단계를 진행하면 된다.
- live-validation-001 / runtime-soak-001 / strategy-002 / paper-002 의 request.ko.md 초안은 본 plan 에서 작성하지 않는다 — master plan §10 의 "동시에 두 개 이상의 Codex 구현 지시 작성 없음" 원칙 준수.
- 본 master plan + codex-task.md 자체는 코드 / catalog 본문 / `.env` / GUI 어떤 파일도 수정하지 않는다.

# api-orders-paper-003-query — Implementation Patch

본 patch 는 roadmap-implementation-plan 의 Phase 1 으로 Claude 가 직접 구현했다 (사용자가 "B" interpretation 선택: Phase 1→2→3 sequential automation).

## 1. Files Changed

- `app/broker/kis.py` — 새 `KisQueryTransport` Protocol + `MockQueryTransport` + `UrllibQueryTransport` (GET 전용, paper 제약 enforcement), 새 상수 (`KIS_OVERSEAS_CCNL_PATH`, `KIS_PAPER_CCNL_TR_ID="VTTS3035R"`, `KIS_PAPER_QUERY_*`), `KisBroker.__init__` 에 `_query_transport` 자동 선택, `KisBroker.get_open_orders` / `get_fills` / `get_order_status` 본문 구현 (NotImplementedError → 실제 fetch + client-side filter/lookup), 신규 helper `_fetch_ccnl_rows` (페이지네이션 + sanitize + paper 제약).
- `tests/test_kis_paper_order_query.py` (NEW) — 30 신규 테스트.
- `tests/test_broker_interface.py` (NARROW) — `test_kis_data_methods_not_implemented` / `test_kis_broker_has_get_fills_and_get_order_status` / `test_kis_protocol_methods_delegate_to_not_implemented` 의 NotImplementedError 단언을 `KisOrderRejectedError("authentication_required")` 로 갱신.
- `tests/test_kis_http_boundaries.py` (NARROW) — `test_cancel_replace_queries_fail_closed` 의 `get_open_orders` / `get_fills` / `get_order_status` `NotImplementedError` 단언을 `KisOrderRejectedError("authentication_required")` 로 갱신. cancel/replace 단언 무변동.
- `tests/test_kis_paper_order_cancel_replace.py` (NARROW) — `test_get_*_still_not_implemented_after_cancel_replace` 3 함수 이름을 `..._requires_auth_after_query_unblocked` 로 변경하고 단언을 `KisOrderRejectedError("authentication_required")` 로 갱신.

## 2. Implementation Summary

- Endpoint: GET `/uapi/overseas-stock/v1/trading/inquire-ccnl` (catalog §4.2).
- Paper TR_ID: `VTTS3035R` (catalog §4.7 / §4.7.1).
- Paper 제약 강제 (catalog §4.7): `PDNO=""`, `SLL_BUY_DVSN="00"`, `CCLD_NCCS_DVSN="00"`, `SORT_SQN="DS"`, `ORD_DT="" / ORD_GNO_BRNO="" / ODNO=""`, 거래소 `NASD`/`NYSE`/`AMEX` 만 (Asia / `%` 금지).
- Response 매핑: catalog §4.7.1 의 `Confirmed: yes` field 만 사용 — `odno`, `pdno`, `sll_buy_dvsn_cd`, `ft_ord_qty`, `ft_ccld_qty`, `nccs_qty`, `ft_ord_unpr3`, `ft_ccld_unpr3`, `ft_ccld_amt3`, `prcs_stat_name`, `ord_tmd`, `ovrs_excg_cd`, `tr_crcy_cd`.
- `get_open_orders` — paper 전체조회 + `nccs_qty > 0` client filter.
- `get_fills` — paper 전체조회 + `ft_ccld_qty > 0` client filter.
- `get_order_status(broker_order_id)` — paper 전체조회 + client-side ODNO lookup. 못 찾으면 `KisOrderRejectedError("unknown_broker_order_id")`.
- 페이지네이션: `ctx_area_fk200` / `ctx_area_nk200` + `KIS_QUERY_MAX_PAGES=10` 안전 cap.
- 모든 응답은 `sanitize_kis_response` 통과 후 보존.
- 미체결/체결/상태 셋 다 PARTIALLY READY 분류 그대로 (KIS_2-check / KIS_3 audit 결정 유지).

## 3. Safety Confirmation

- 실전 TR_ID (`TTTS3035R`, `TTTS3018R` 등) 코드 / 테스트 / docs 에 0 lines. 본 patch 의 forbidden literal 검증 테스트가 string concatenation 으로 작성됨.
- 모의 미지원 endpoint (`inquire-nccs`) 호출 코드 0 lines.
- `KIS_PAPER_QUERY_EXCHANGES = {"NASD", "NYSE", "AMEX"}` — Asia / `%` 거부.
- 외부 HTTP 라이브러리 (`requests` / `httpx` / `aiohttp` / `urllib3` / `openpyxl` / `pandas`) import 없음.
- `capabilities()` 의 `open_orders` / `fills` / `order_status` 플래그 `False` 유지 (status surface 보존).
- `healthcheck()["order_execution_implemented"]` `False` 유지.
- `validate_kis_order_request` / `_validate_paper_settings` / `OrderType.MARKET` 가드 / `ALLOW_MARKET_ORDERS=true` reject / kill switch 변경 없음.
- `OrderType.STOP` 미도입.
- FX 변환 도입 없음.
- `app/broker/kis_http.py` 무변동.
- `.env` / `.env.example` / `app/config.py` 무변동 (새 env 변수 없음).
- `app/api/*`, `app/static/*`, `app/main.py` 무변동.
- Strategy / Agent / LLM 의 `app.broker.kis` 직접 import 없음.
- secret / 계좌번호 / token / Bearer 노출 없음 (`_RaiseOnCallOrderTransport`-style fake + `sanitize_kis_response` + repr/exception 회귀 테스트).

## 4. Test Results

```text
$ .venv/bin/python -m compileall app tests
PASS

$ .venv/bin/python -m pytest -p no:cacheprovider tests/test_kis_paper_order_query.py
30 passed in 0.05s

$ .venv/bin/python -m pytest -p no:cacheprovider
488 passed in 0.74s  ← baseline 458 + new 30
```

(Phase 2 / 3 이후 최종 카운트는 520. 본 Phase 1 단독 직후의 carve-out 결과 488.)

## 5. Remaining TODOs

- Status-surface job (별도) — `capabilities()["open_orders"]`/`["fills"]`/`["order_status"]` 를 advertise True 로 바꾸려면 `app/api/routes.py` 갱신 필요. 현재 보수적 `False` 유지.
- OMS protocol 확장 (별도) — `OMS.get_fills` / `OMS.get_open_orders` 진입점을 만들 경우.
- 응답 행을 풍부한 도메인 모델 (Fill / OpenOrder dataclass) 로 변환하는 보강 (별도).

Verdict: READY FOR REVIEW (인-conversation 자체 검증 완료, commit 은 사용자).

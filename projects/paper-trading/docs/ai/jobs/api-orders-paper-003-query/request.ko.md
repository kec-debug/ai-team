# 작업 ID
api-orders-paper-003-query

# 작업명
KIS 모의투자 주문 조회 기능 구현 (adapter-level partial query)

KIS_3 에서 `docs/kis/MISSING_OFFICIAL_VALUES.md` §4.7.1 이 보강되었다. `VTTS3035R` 주문체결내역 response `output[]` sub-field 이름이 확인되어 `get_open_orders()`, `get_fills()`, `get_order_status()` 의 adapter-level 부분 구현이 가능해졌다.

단, 모든 기능은 paper 제약 때문에 PARTIALLY READY 이다.

- `get_open_orders`: native `/inquire-nccs` 는 모의 미지원. `/inquire-ccnl` 전체 조회 후 `nccs_qty` / `prcs_stat_name` 기반 client-side filtering 만 허용.
- `get_fills`: 별도 fill id / 명확한 체결시각 field 는 확인되지 않음. `odno` + `ft_ccld_qty` / `ft_ccld_unpr3` / `ft_ccld_amt3` 기반 projection 또는 sanitized broker row 반환으로 제한.
- `get_order_status`: 별도 주문상태 endpoint 및 paper ODNO query 없음. 전체 조회 후 client-side ODNO lookup 만 허용. 조회 범위 밖이면 fail-closed.

## 목표

- `KisBroker.get_open_orders()` 를 catalog §4.7 + §4.7.1 의 `Confirmed: yes` 필드만 사용해 구현한다.
- `KisBroker.get_fills()` 를 catalog §4.7 + §4.7.1 의 `Confirmed: yes` 필드만 사용해 구현한다.
- `KisBroker.get_order_status(broker_order_id)` 를 catalog §4.7 + §4.7.1 의 `Confirmed: yes` 필드만 사용해 구현한다.
- 세 메서드는 모두 adapter-level only 로 구현한다. OMS protocol 확장 없음.
- GUI / status surface / capabilities 공개 변경 없음. `capabilities()["open_orders"]`, `["fills"]`, `["order_status"]` 는 별도 status-surface job 전까지 `False` 유지.
- query 는 GET 이므로 새 `KisQueryTransport` Protocol 또는 동등한 GET 전용 transport 를 추가한다. 기존 `KisOrderTransport` 는 POST 전용이므로 재사용하지 않는다.

## 사용할 catalog 값

사용 가능:

- Endpoint: GET `/uapi/overseas-stock/v1/trading/inquire-ccnl`
- Paper TR_ID: `VTTS3035R`
- Request fields: §4.7 의 `CANO`, `ACNT_PRDT_CD`, `PDNO`, `ORD_STRT_DT`, `ORD_END_DT`, `SLL_BUY_DVSN`, `CCLD_NCCS_DVSN`, `OVRS_EXCG_CD`, `SORT_SQN`, `ORD_DT`, `ORD_GNO_BRNO`, `ODNO`, `CTX_AREA_NK200`, `CTX_AREA_FK200`
- Paper constraints: `PDNO=""`, `SLL_BUY_DVSN="00"`, `CCLD_NCCS_DVSN="00"`, `SORT_SQN` default `DS`, `ORD_DT=""`, `ORD_GNO_BRNO=""`, `ODNO=""`
- Response top-level fields: `rt_cd`, `msg_cd`, `msg1`, `ctx_area_fk200`, `ctx_area_nk200`, `output[]`
- Response `output[]` fields from §4.7.1 only, including `ord_dt`, `odno`, `orgn_odno`, `sll_buy_dvsn_cd`, `pdno`, `ft_ord_qty`, `ft_ord_unpr3`, `ft_ccld_qty`, `ft_ccld_unpr3`, `ft_ccld_amt3`, `nccs_qty`, `prcs_stat_name`, `rjct_rson`, `rjct_rson_name`, `ord_tmd`, `ovrs_excg_cd`, `tr_crcy_cd`

사용 금지:

- `/inquire-nccs` (`TTTS3018R`) in paper. §4.8 에 따라 모의 미지원.
- Live TR_IDs.
- Paper-unsupported TR_IDs.
- Asia paper TR_ID 추측.
- §4.7.1 에 없는 response field 추측.

## 절대 하지 말 것

- live trading 활성화 금지.
- 실전 endpoint / 실전 TR_ID 사용 금지.
- KIS endpoint, TR ID, payload, header, response field 추측 금지.
- `/inquire-nccs` 를 paper query 에 사용 금지.
- `CCLD_NCCS_DVSN="01"` 또는 `"02"` 를 paper query 에 사용 금지. Paper 는 `"00"` 전체만 허용.
- `ODNO` query parameter 로 단건 검색 시도 금지. Paper 는 반드시 `""`.
- 외부 HTTP 라이브러리 사용 금지. stdlib `urllib.request` 만 허용.
- `requests`, `httpx`, `aiohttp`, `urllib3` 추가 금지.
- `openpyxl`, `pandas` 추가 금지.
- OMS protocol 확장 금지.
- GUI / API / status surface 변경 금지.
- `capabilities()` / `healthcheck()` 공개 surface 변경 금지.
- Strategy, Agent, LLM 이 broker 를 직접 호출하는 경로 추가 금지.
- OMS / RiskEngine 우회 금지.
- `OrderType.MARKET` 3중 가드 우회 금지.
- `ALLOW_MARKET_ORDERS=true` 허용 금지.
- `.env` / `.env.example` 수정 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호 기록 금지.
- payment, auth settings, production infra, database migrations 변경 금지.
- 자동 git commit / push / merge / PR / production deploy 금지.

## 구현 지침

- `app/broker/kis.py` 내부에 GET 전용 query transport 를 추가한다.
- `KisAccountTransport` / `UrllibAccountTransport` 패턴을 재사용한다.
- query transport allowlist:
  - paper host only: `openapivts.koreainvestment.com:29443`
  - path only: `/uapi/overseas-stock/v1/trading/inquire-ccnl`
  - method only: GET
  - TR_ID only: `VTTS3035R`
  - exchange only: paper-supported US set (`NASD`, `NYSE`, `AMEX`) or catalog-confirmed `%` if explicitly chosen in plan
  - paper constraints exactly as §4.7
- Pagination must use only `ctx_area_fk200` / `ctx_area_nk200` and bounded page caps.
- Every raw response must be passed through `sanitize_kis_response`.
- Missing `rt_cd` or malformed `output` must fail closed.
- KIS error `rt_cd != "0"` must fail closed with short `KisOrderRejectedError("kis_error:<code>")` style.
- Query range must be conservative and deterministic. If a broker order id cannot be found in the allowed fetched window, fail closed rather than guessing.

## 완료 기준

- `get_open_orders()` works through `VTTS3035R` total query + client-side filter only.
- `get_fills()` works through `VTTS3035R` total query and maps only confirmed fields.
- `get_order_status(broker_order_id)` works through `VTTS3035R` total query + client-side lookup only.
- Any unsupported mapping remains fail-closed with a short tag.
- `/inquire-nccs` stays unimplemented for paper.
- No OMS/runtime/GUI/status-surface integration.
- `capabilities()` flags stay `False`.
- `healthcheck()["order_execution_implemented"]` stays consistent with prior conservative surface unless a separate approved status job changes it.
- Tests cover transport allowlists, paper constraints, pagination cap, malformed responses, KIS errors, sanitization, secret-safe repr/exception, and Strategy/Agent isolation.
- Full checks pass:
  - `.venv/bin/python -m compileall app tests`
  - `.venv/bin/python -m pytest -p no:cacheprovider`

## patch.md must include

- Files changed.
- Catalog rows used from §4.7 / §4.7.1.
- Explicit partial-readiness limitations.
- Query transport allowlists.
- Safety confirmations.
- Test results.
- Safety grep outputs.
- Claude verification prompt.
- Follow-up Codex prompt rules.

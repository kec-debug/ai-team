# api-orders-paper-002-cancel-replace — request.ko.md 초안

본 파일은 KIS_2-check audit (`docs/ai/jobs/KIS_2-check/plan.md`) 의 권고에 따라 작성된 **다음 job 의 request.ko.md 초안**이다. 사용자가 검토 후 그대로 또는 수정하여 `projects/paper-trading/docs/ai/jobs/api-orders-paper-002-cancel-replace/request.ko.md` 로 옮기면 다음 turn 에서 Claude 가 plan + codex-task 단계로 진행할 수 있다.

본 audit 자체는 코드 변경을 수행하지 않는다 — 이 초안 파일은 다음 job 의 입력일 뿐이며, 본 turn 의 Codex 가 실행할 작업은 아니다.

---

```markdown
# 작업 ID
api-orders-paper-002-cancel-replace

# 작업명
KIS 모의투자 주문 정정·취소 구현 (cancel_order / replace_order)

KIS_2-check audit (`docs/ai/jobs/KIS_2-check/plan.md`, `recommendation.md`) 에서 정리한 결과, `docs/kis/MISSING_OFFICIAL_VALUES.md` §4.2 / §4.6 의 paper-supported 정정·취소 endpoint 가 `Confirmed: yes` 상태로 충분히 채워져 있다. api-orders-paper-001 에서 `place_order()` 본문이 paper 모드 dry-run + 실제 모의 주문 전송 모두 안전 가드를 통과해 구현되었고, 본 작업은 그 위에 **취소 / 정정** 기능을 추가한다.

이번 작업은 실전거래가 아니라 KIS 모의투자 정정·취소 검증이다. live trading 은 계속 비활성이며, 모든 정정·취소 호출은 OMS 가 만든 BrokerOrder 또는 broker_order_id 만 사용하며, Strategy / Agent / LLM 이 broker 를 직접 호출하지 않는다.

`get_open_orders()` / `get_fills()` / `get_order_status()` 는 KIS_2-check audit 에서 **BLOCKED-BY-DOCS** 로 분류되었으므로 본 작업 범위 밖이다. 해당 3 개 메서드는 fail-closed (NotImplementedError) 를 유지한다.

## 목표

- `KisBroker.cancel_order(broker_order_id)` 본문을 KIS 모의투자 정정취소 endpoint 기반으로 구현한다.
- `KisBroker.replace_order(broker_order_id, broker_order)` 본문을 KIS 모의투자 정정 endpoint 기반으로 구현한다.
- KIS_2 에서 `Confirmed: yes` 로 정리된 endpoint / TR_ID / headers / request fields / response fields 만 사용한다 (catalog §4.2, §4.6).
  - 모의 endpoint: `POST /uapi/overseas-stock/v1/trading/order-rvsecncl`
  - 모의 TR_ID (US 정정·취소 공용): `VTTT1004U`
- stdlib `urllib.request` 기반 기존 HTTP 경계만 사용. 외부 HTTP 라이브러리 추가 금지.
- 어댑터 내부에 `_order_history: dict[broker_order_id, KisOrderResponse]` (또는 동등한 좁은 상태) 를 도입해 정정·취소 시 필요한 (symbol, ORGN_ODNO, 원 ORD_QTY) 를 lookup 한다. 이력 dict 는 메모리 안에서만 보관되며 `.env` / 디스크 / 외부 저장소에 기록되지 않는다.
- `KIS_ORDER_DRY_RUN=true` 기본값을 유지한다. dry-run true 면 실제 HTTP 정정·취소가 나가지 않고 sanitized preview 만 반환한다.
- dry-run false 인 경우에도 `TRADING_MODE=paper`, `LIVE_TRADING_ENABLED=false`, `KIS_ENV=paper`, `kill_switch_engaged=false`, paper-supported 거래소 / LIMIT 만 조건을 모두 만족해야만 모의 정정·취소가 전송된다.
- raw response 는 `sanitize_kis_response` 를 통한 sanitized 형태로만 보관한다.
- app key, app secret, access token, Bearer token, 계좌번호 원문은 코드 / 로그 / 응답 / 예외 / 테스트 / patch 어디에도 노출하지 않는다.
- 테스트를 추가한다.

## 사용할 공식 catalog 값 (KIS_2-check audit 기준)

### endpoint (`docs/kis/MISSING_OFFICIAL_VALUES.md` §4.2, §4.6)

- path: `/uapi/overseas-stock/v1/trading/order-rvsecncl` — Confirmed: yes
- HTTP method: POST — Confirmed: yes
- paper TR_ID (US 정정·취소 공용): `VTTT1004U` — Confirmed: yes
- base URL (paper): `https://openapivts.koreainvestment.com:29443` — Confirmed: yes

### Request headers (§4.3 = §2.3)

- `content-type: application/json; charset=utf-8`
- `authorization: Bearer ${access_token}`
- `appkey`
- `appsecret`
- `tr_id: VTTT1004U`
- (옵션) `tr_cont`, `custtype`, `personalseckey`, `seq_no`, `mac_address`, `phone_number`, `ip_addr`, `gt_uid` — 본 작업은 개인 사용자 가정으로 미설정

### Request body (§4.6, 모두 Confirmed: yes)

- `CANO`: 종합계좌번호 앞 8 자리 (필수)
- `ACNT_PRDT_CD`: 계좌상품코드 뒤 2 자리 (필수)
- `OVRS_EXCG_CD`: paper 는 `NASD` / `NYSE` / `AMEX` (필수)
- `PDNO`: 종목코드 (필수, 원주문의 PDNO)
- `ORGN_ODNO`: 원주문번호 (필수, `/order` 응답의 `output.ODNO`)
- `RVSE_CNCL_DVSN_CD`: 정정·취소 구분 (필수)
  - 취소: `"02"`
  - 정정: `"01"`
- `ORD_QTY`: 주문수량 (필수)
  - 취소 시: 원주문의 수량
  - 정정 시: 정정 후 수량
- `OVRS_ORD_UNPR`: 단가 (필수)
  - 취소 시: 반드시 `"0"`
  - 정정 시: 정정 후 단가
- (옵션) `MGCO_APTM_ODNO`, `ORD_SVR_DVSN_CD` — 본 작업 미설정

### Response body (§4.6 = §4.5 형태, 모두 Confirmed: yes)

- `rt_cd`: `"0"`=성공, 그 외=실패
- `msg_cd`, `msg1`: 응답 코드 / 메시지
- `output.KRX_FWDG_ORD_ORGNO`: 영업점코드 (string 5)
- `output.ODNO`: 정정·취소 결과 주문번호 (string 10) — broker_order_id_after_rvsecncl 후보
- `output.ORD_TMD`: 주문시각 `HHMMSS`

## 절대 하지 말 것

- live trading 활성화 금지.
- 실전 정정취소 endpoint 또는 실전 TR_ID (`TTTT1004U`, `TTTS1003U`, `TTTS0309U` 등) 사용 금지.
- 본 작업 외 endpoint (`/order`, `/inquire-ccnl`, `/inquire-nccs`, `/order-resv*`, `/daytime-order*`, `/algo-ordno`, `/inquire-algo-ccnl`) 추가·수정 금지.
- KIS endpoint, TR ID, payload, header, response field 추측 금지. catalog `Confirmed: yes` 행 외 사용 금지.
- 모의 미지원 endpoint 호출 금지 (`TTTS3018R` 등).
- `get_open_orders()` / `get_fills()` / `get_order_status()` 본문 구현 금지 — 본 작업 범위 밖. NotImplementedError 또는 fail-closed 유지.
- 외부 HTTP 라이브러리 (`requests`, `httpx`, `aiohttp`, `urllib3`) import 금지.
- Strategy / Agent / LLM 이 broker 또는 KisBroker 를 직접 호출하는 경로 추가 금지.
- OMS / RiskEngine 우회 금지. cancel / replace 모두 OMS 또는 신뢰된 호출 경로 (예: 관리자 dashboard) 에서만 진입.
- `ALLOW_MARKET_ORDERS=true` 허용 금지. `OrderType.MARKET` / `OrderType.STOP` 도입 금지.
- FX 변환 함수 / 환율 상수 도입 금지.
- `.env` / `.env.example` 읽기·수정 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호 코드 / 문서 / 테스트 / patch 기록 금지.
- GUI 파일 (`app/api/`, `app/static/`, `app/main.py`) 수정 금지. `capabilities()` 의 `cancel` / `replace` 플래그는 conservative `False` 유지 (status surface 회귀 보호 — api-orders-paper-001 동일 정책).
- 자동 git commit / push / merge / deploy 금지.

## 완료 기준

- `KisBroker.cancel_order(broker_order_id)` 가 catalog §4.6 기반으로 구현된다.
- `KisBroker.replace_order(broker_order_id, broker_order)` 가 catalog §4.6 기반으로 구현된다.
- dry-run true 에서는 실제 HTTP 정정·취소가 나가지 않고 sanitized preview + dry-run ack 만 반환.
- dry-run false 에서는 paper / live-off / kis_env=paper / kill_switch=off / paper-supported 거래소 / LIMIT 모든 가드를 통과할 때만 전송 경계에 도달한다.
- 원주문 lookup 실패 시 `KisOrderRejectedError("unknown_broker_order_id")` 로 fail-closed.
- 모의 미허용 거래소 / 비-paper TR_ID / 잘못된 ORD_DVSN 등 transport 차단 가드가 cancel·replace 경로에도 동일 적용된다.
- response parser 는 catalog §4.5 / §4.6 의 `Confirmed: yes` 필드만 사용.
- raw response 는 sanitized 처리되어 `_last_order_response` (또는 `_order_history`) 에 저장.
- secret / 계좌번호 / token 원문 비노출.
- Strategy / Agent / LLM 가 broker 를 직접 호출하지 않음 (기존 회귀 유지).
- `get_open_orders()` / `get_fills()` / `get_order_status()` 는 이번 작업에서 변경되지 않는다 (NotImplementedError 유지).
- 전체 pytest 회귀 0 건.
- 안전 grep clean (실전 TR_ID / 모의 미지원 TR_ID / live base URL / external HTTP 0 lines).
- `patch.md` 에 다음 항목 포함:
  - 수정 파일 목록
  - 사용한 공식 정정취소 endpoint / TR_ID 출처
  - dry-run 동작 방식
  - 실 모의 정정·취소 전송 조건
  - cancel / replace 시 원주문 lookup 정책
  - fail-closed 로 남긴 항목 (`get_open_orders` / `get_fills` / `get_order_status`)
  - secret / account / token 노출 없음 확인
  - live trading 비활성 유지 확인
  - market order guard 유지 확인
  - 테스트 결과
  - 안전 grep 결과
  - Claude 검증 요청 프롬프트
  - Claude 리뷰가 REQUEST CHANGES / BLOCK 일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙

## 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

전체 PASS 가 완료 조건.
```

---

## 본 audit 의 비고

- 본 codex-task.md 는 **`api-orders-paper-002-cancel-replace` 의 request.ko.md 초안**이며, KIS_2-check audit 자체의 Codex 작업은 아니다. 사용자가 그대로 새 job 디렉터리로 옮길 때까지는 어떤 Codex 도 본 파일을 실행하지 않는다.
- `get_open_orders` / `get_fills` / `get_order_status` 의 후속 job 은 별도로 `KIS_3-inquire-ccnl-output-fields` (catalog 보강) 가 완료된 뒤 `api-orders-paper-002-query-only` 로 진행 권고. 본 audit 는 해당 후속 job 의 request.ko.md 초안을 작성하지 않는다 (catalog 가 아직 차단된 상태).
- 본 audit 자체는 코드 / catalog / `.env` / GUI 모두 무변동.

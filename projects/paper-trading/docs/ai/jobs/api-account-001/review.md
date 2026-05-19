# api-account-001 — Claude Review (final)

## Verdict

APPROVE

## Summary

api-account-001 implements KIS 모의투자 read-only 계좌 / 잔고 / 포지션 조회 strictly against the `Confirmed: yes` paper-supported rows in `docs/kis/MISSING_OFFICIAL_VALUES.md` §2 (잔고 `VTTS3012R`). Follow-up 1 surgically updated the catalog-state regression test to match the post-KIS_2 catalog reality while keeping real-credential-prefix leak protection intact. Full pytest is clean (366 passed, 0 failed).

## Scope of changes in this job

In-scope, intentional (by api-account-001 and its Follow-up 1):

- `projects/paper-trading/app/broker/kis.py` — KisAccountTransport / Mock·UrllibAccountTransport, `_split_kis_account_no`, `KisPosition` 확장 (`currency` / `exchange`), `KisAccountClient` 구현 (`get_account` / `get_positions` / `get_cash_balance`), `parse_positions_response` 재작성, `parse_cash_balance_response` fail-closed.
- `projects/paper-trading/tests/test_kis_account_client.py` — 23 신규/갱신 함수: split / auth / paper-only / mock fail-closed / single-page / pagination / cap / kis_error / catalog field mapping / multi-currency / urllib host / TR_ID / exchange / currency allowlists / cash fail-closed / parser catalog-only / sanitization / repr & exception secret leak / KisBroker healthcheck.
- `projects/paper-trading/tests/test_kis_http_boundaries.py` — `test_account_parsers_return_internal_models_and_sanitize` 한 함수만 catalog 필드명 정렬 (`ovrs_pdno` 등) + cash 검증을 `KisDataUnavailableError("paper_cash_balance_not_available_official_field_missing")` 로 변경.
- `projects/paper-trading/tests/test_missing_official_values_doc.py` — Follow-up 1: `test_missing_official_values_does_not_leak_real_secrets` 의 `Confirmed: yes` assertion 제거 + vendor 경로/도메인 forbidden entries (`/uapi/`, `/oauth2/`, `paper-api`, `koreainvestment.com`) 제거. 실제 credential prefix entries (`PSNFD`, `PKID`, `AKIA`, `sk-`, `ghp_`) 와 `"<TBD>" in text` 단언은 유지.
- `projects/paper-trading/docs/ai/jobs/api-account-001/patch.md` — 본 job 작성.

Out-of-scope, pre-existing dirty (NOT caused by this job — present in conversation-start `git status`):

- `projects/paper-trading/app/api/server.py`
- `projects/paper-trading/scripts/_common.sh`
- `projects/paper-trading/scripts/start_server.sh`
- `docs/ai/jobs/mvp-002/request.ko.md`

확인 대상으로 명시된 다음 파일들은 **변경 없음**:

- `projects/paper-trading/app/broker/base.py` — 변경 없음.
- `projects/paper-trading/app/config.py` — 변경 없음.
- `projects/paper-trading/README.md` — 변경 없음 (plan §3 의 선택적 갱신이었으며 미수행으로 OK).
- `projects/paper-trading/app/broker/kis_http.py` — 변경 없음. `ALLOWED_PATHS_API_AUTH_001` 그대로 `{/oauth2/tokenP, /oauth2/revokeP}`.
- `projects/paper-trading/app/api/*` (server.py 외) / `app/static/*` / `app/main.py` — 변경 없음.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` — 변경 없음.
- `.env` / `.env.example` — 변경 없음.

## Review focus 항목별 결론

1. **Only confirmed KIS account / catalog values were used.** OK. `KIS_OVERSEAS_BALANCE_PATH = "/uapi/overseas-stock/v1/trading/inquire-balance"`, `KIS_OVERSEAS_BALANCE_TR_ID_PAPER = "VTTS3012R"` 만 도입. 응답 매핑은 `output1[].ovrs_pdno` / `ovrs_cblc_qty` / `pchs_avg_pric` / `ovrs_stck_evlu_amt` / `tr_crcy_cd` / `ovrs_excg_cd` 와 `output2`, `rt_cd`, `msg_cd`, `msg1`, `ctx_area_fk200`, `ctx_area_nk200` 만 사용 — 모두 catalog §2.4 / §2.5 의 `Confirmed: yes` 행.

2. **No KIS endpoint / TR ID / header / payload / response field was invented.** OK. 실전 TR_ID (`TTTS3012R` / `CTRP6504R` / `CTRP6010R` / `CTOS4001R` / `TTTS3039R` / `TTTC2101R`) 및 모의 미지원 TR_ID (`TTTS3018R` / `TTTT3039R` / `TTTS3014R` / `TTTS6036U` / `TTTS6037U` / `TTTS6038U` / `TTTS6058R` / `TTTS6059R`) 모두 코드/테스트/문서에 추가 없음. legacy 추측 필드 (`pdno` / `hldg_qty` / `qty` / `dnca_tot_amt` / `nxdy_excc_amt` / generic `symbol` / `quantity` / `avg_price` / `market_value` / `crcy_cd` / `cash` dict alias) 모두 parser 에서 제거.

3. **No real app key / app secret / account number / token / Bearer token is exposed.** OK. fixtures 는 명백한 가짜 (`fake-key-XYZ`, `fake-secret-XYZ`, `12345678-01`, `fake-access-token`, `Bearer test-token`). `sanitize_kis_response` 가 응답의 sensitive 키 (`appkey` / `appsecret` / `access_token` / `account_no` / `cano` / `authorization` 등) 와 settings 의 secret 값을 redact. `__repr__` / exception message / pytest capture 어디에도 noise 없음 — `test_account_client_repr_and_exceptions_do_not_expose_secrets` 와 `test_get_account_sanitizes_echoed_secrets` 가 회귀로 단언.

4. **.env was not read / modified / added / printed.** OK. `app/config.py` 무변동. `_split_kis_account_no` / transport 클래스 / KisAccountClient 어디에서도 `.env` 또는 `dotenv` 호출 없음. settings 값만 사용.

5. **Live trading remains disabled.** OK. `LIVE_TRADING_ENABLED` 활성화 코드 없음. live TR_ID / live base URL (`openapi.koreainvestment.com:9443`) 호출 추가 없음. `_validate_paper_account_query()` 가 `trading_mode_not_paper` / `live_trading_enabled` / `kis_env_not_paper` / `kill_switch_engaged` 위반 시 `KisAuthError` 로 read-only 조회까지 차단 (회귀 테스트로 검증).

6. **Market orders remain guarded.** OK. `validate_kis_order_request()` / `OrderType.MARKET` 3중 가드 / `ALLOW_MARKET_ORDERS=true` reject / kill switch 동작 변경 없음. `capabilities()` 의 `submission` / `cancel` / `replace` / `open_orders` / `fills` / `order_status` 전부 False 유지.

7. **No order HTTP implementation was added.** OK. `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 본문·예외 동작 무변동. `_to_kis_request` / `_dry_run_preview` / `last_order_preview` 무변동.

8. **Account / positions / cash methods are read-only.** OK. `get_account()` / `get_positions()` 는 GET only (`UrllibAccountTransport.get_balance` 의 `Request(..., data=None, method="GET")`). 부수효과는 `_account_loaded` / `_positions_loaded` flag 만 갱신. `get_cash_balance()` 는 HTTP 호출 없이 즉시 fail-closed.

9. **Fail-closed behavior remains when official values are missing.** OK. `get_cash_balance()` 가 `KisDataUnavailableError("paper_cash_balance_not_available_official_field_missing")` 로 fail-closed; `_cash_balance_loaded` False 유지 (catalog 가 paper-supported 에서 (cash, withdrawable_cash) pair 를 보장하지 않음 — `VTTS3007R` 는 per-symbol buying power, `VTRP6504R` paper `output3` sub-field 는 `<TBD>`). `parse_cash_balance_response` 도 동일 메시지로 fail-closed. 페이지 cap 초과 시 `balance_pagination_cap_exceeded`. `kis_error:<msg_cd>` / `invalid_exchange` / `invalid_currency` / `disallowed_host` / `disallowed_tr_id` / `http_<code>` / `transport_error` / `invalid_response_body` 모두 짧은 tag fail-closed.

10. **Strategy / Agent / LLM do not call KIS directly.** OK. patch §3 의 `grep -rn "from app.broker.kis" app/strategy` / `app/agent` 결과 0 lines. 본 job 은 Strategy / Agent 경로에 어떤 import 도 추가하지 않음.

11. **OMS / RiskEngine boundaries were not weakened.** OK. `app/oms/*` / `app/risk/*` / `app/portfolio/*` / `app/runtime/*` / `app/session/*` / `app/strategy/*` 모두 변경 없음. `validate_kis_order_request` (RiskEngine pre-flight) 무변동. Strategy → RiskEngine → OMS → PaperBroker / KisBroker 순서 정책 그대로.

12. **Updated `test_missing_official_values_doc.py` still blocks real credential leaks while allowing confirmed official catalog values.** OK. Follow-up 1 의 diff:
    - 제거: `assert "Confirmed: yes" not in text` (KIS_2 가 catalog 에 의도적으로 confirmed 행을 채웠음).
    - 제거: `forbidden_values` 에서 `"/uapi/"` / `"/oauth2/"` / `"paper-api"` / `"koreainvestment.com"` — catalog 의 합법적 official path / 도메인.
    - **유지**: `forbidden_values` 에 `"PSNFD"` / `"PKID"` / `"AKIA"` / `"sk-"` / `"ghp_"` — 실제 credential / token prefix 의 leak 회귀는 그대로.
    - **유지**: `assert "<TBD>" in text` — catalog §1 (OAuth) / §3 (시세) 등에 여전히 TBD 행이 남아 있어 의미 있는 회귀.
    - `test_missing_official_values_file_exists` 와 `test_missing_official_values_has_required_sections` 무변동.
    이 갱신은 F1 REQUEST_CHANGES 의 권고와 정확히 일치하며 catalog 의 합법 상태를 허용하면서도 실제 credential prefix leak 은 계속 차단한다.

13. **Tests passed: 366 passed.** OK. 자체 검증:
    ```text
    $ .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q
    ........................................................................ [ 19%]
    ........................................................................ [ 39%]
    ........................................................................ [ 59%]
    ........................................................................ [ 78%]
    ........................................................................ [ 98%]
    ......                                                                   [100%]
    366 passed in 0.68s
    ```
    `compileall app tests` 도 PASS.

14. **Scope stayed within api-account-001.** OK. 본 job 의 in-scope diff 는 `app/broker/kis.py` + `tests/test_kis_account_client.py` + `tests/test_kis_http_boundaries.py` (좁은 갱신) + `tests/test_missing_official_values_doc.py` (Follow-up 1, F1 권고 정렬) + `docs/ai/jobs/api-account-001/patch.md` 다섯 개. `app/broker/base.py` / `app/config.py` / `README.md` / `app/broker/kis_http.py` / `app/broker/kis_quote_mapper.py` / `app/broker/kis_token_cache.py` / `app/broker/paper.py` / `app/broker/alpaca_paper.py` / `app/oms/*` / `app/risk/*` / `app/portfolio/*` / `app/runtime/*` / `app/session/*` / `app/strategy/*` / `app/agent*` / `app/main.py` / `app/api/routes.py` / `app/static/*` / `docs/kis/MISSING_OFFICIAL_VALUES.md` / `.env` / `.env.example` 모두 변경 없음. 워킹 트리에 남은 `app/api/server.py` / `scripts/_common.sh` / `scripts/start_server.sh` / `docs/ai/jobs/mvp-002/request.ko.md` 의 modification 은 conversation-start 시점부터 존재하던 별건 작업으로 본 job 과 무관.

## Test verification (재실행 결과)

```text
$ .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q
366 passed in 0.68s
```

api-account-001 신규/갱신 테스트 (37 함수) + 갱신된 `test_missing_official_values_does_not_leak_real_secrets` 포함 전체 회귀 통과.

## Remaining TODOs (후속 job 영역)

- `api-cash-balance-001` (가칭): `VTRP6504R` paper `output3` sub-field 가 KIS_2 patch.md §5 의 `<TBD>` 에서 catalog 확정되면 `get_cash_balance()` 를 잔고 endpoint 와 분리해서 구현 가능.
- `api-buying-power-001` (가칭): `VTTS3007R` (per-symbol 매수가능금액) 은 의미가 `KisCashBalance` 와 다르므로 별도 모델 + 메서드로 분리.
- 잔고 endpoint 의 `output2` 집계 필드 (`tot_evlu_pfls_amt` / `tot_pftrt` / `ovrs_tot_pfls`) 를 PortfolioService 로 노출하는 read-only 통합도 후속 job 영역 (본 job 은 raw `output2` 만 반환).

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| 1. confirmed catalog values only | OK |
| 2. no invented endpoint / TR_ID / header / field | OK |
| 3. no secret / app key / app secret / 계좌번호 / token / Bearer leak | OK |
| 4. `.env` 무변동 | OK |
| 5. live trading 비활성 유지 | OK |
| 6. market order 가드 유지 | OK |
| 7. order HTTP 미구현 | OK |
| 8. account / positions / cash 모두 read-only | OK |
| 9. catalog 부족 시 fail-closed (cash, pagination, malformed) | OK |
| 10. Strategy / Agent / LLM 가 KIS 직접 호출 안 함 | OK |
| 11. OMS / RiskEngine 경계 변동 없음 | OK |
| 12. `test_missing_official_values_doc.py` 가 real credential 차단 + confirmed 값 허용 | OK |
| 13. pytest 366 passed | OK |
| 14. scope 가 api-account-001 안에 머묾 | OK |
| 자동화 금지 (commit / push / merge / deploy) | 수행 안 됨 |

## Follow-up Codex prompt

없음. APPROVE.

다음 단계는 사람이 직접 `git diff` 로 변경 범위를 한 번 더 확인하고 (선택적으로 KisBroker / KisAccountClient 의 변경 부분을 spot-check) `git add` → `git commit` 을 수동 실행하는 것이다. 본 review 는 commit / push / merge / deploy 를 수행하지 않으며, 그 책임은 사람에게 있다.

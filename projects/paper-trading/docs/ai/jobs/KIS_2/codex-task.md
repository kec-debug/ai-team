# Codex 작업 지시문 — KIS_2

## 0. 본 작업의 전제

- 상위 plan: `projects/paper-trading/docs/ai/jobs/KIS_2/plan.md`.
- 사용자 업로드: `uploads/6.xlsx` — 2026-05-19 사용자 확인 KIS 공식 자료. **Codex 는 이 xlsx 를 다시 파싱하지 말 것**. 필요한 모든 값은 본 codex-task 의 §A 본문에 byte-level 그대로 박혀 있다.
- 코드 변경 0건. 본 작업은 **문서 1 개 (`docs/kis/MISSING_OFFICIAL_VALUES.md`) + patch.md 1 개**만 변경.
- `pytest` 실행은 본 job 완료 조건이 아니지만 회귀 안전을 위해 `python -m compileall app tests` 는 실행한다.

## 1. Hard rules (안전)

- KIS endpoint URL / TR ID / 헤더 / 응답 필드명 추측 금지. **본 codex-task 의 §A 본문을 byte-level 그대로** `docs/kis/MISSING_OFFICIAL_VALUES.md` §2 와 §4 에 적용. 다른 값 추가 금지.
- 실 app key / app secret / 계좌번호 / access token / refresh token / Bearer 값 **기록 금지** (본문에 없으며, 어떤 자리에도 추가하지 말 것).
- `app/` 하 코드, `app/broker/kis*.py`, `app/domain/`, `app/oms/`, `app/risk/`, `app/portfolio/`, `app/strategy/`, `app/session/`, `app/runtime/`, `app/api/`, `app/static/`, `app/main.py`, `app/config.py`, `tests/`, `.env`, `.env.example`, `.gitignore`, `pyproject.toml`, `pytest.ini`, `README.md` **변경 금지**.
- `docs/kis/MISSING_MARKET_DATA_VALUES.md` **변경 금지**.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` 의 §1 / §3 / "정책" / "다음 작업 가이드" / "보안" 섹션 **변경 금지**. 본 작업은 §2 와 §4 두 섹션 본문만 교체.
- 외부 HTTP 라이브러리 import 추가 금지. 실 KIS 호스트로 네트워크 호출 금지.
- 실주문 / 시장가 주문 / RiskEngine 우회 / OMS 우회 / Strategy 의 broker 직접 호출 / Agent 의 executable order 생성 금지.
- 자동 `git commit` / `push` / `merge` / 배포 금지.

## 2. 수정·생성 파일 화이트리스트

수정 (MODIFY):

- `docs/kis/MISSING_OFFICIAL_VALUES.md` — §2 와 §4 본문 교체.

생성 (NEW):

- `projects/paper-trading/docs/ai/jobs/KIS_2/patch.md` — §A.3 양식 그대로.

위 두 파일 외 어떤 파일도 변경/생성하지 않는다.

## 3. 단계별 작업

### 3.1 §2 본문 교체

`docs/kis/MISSING_OFFICIAL_VALUES.md` 안에서 `## 2. 해외주식/미국주식 계좌` 헤딩부터 그 섹션이 끝나는 `## 3. 해외주식/미국주식 시세` 헤딩 **직전**까지의 모든 줄을 §A.1 본문으로 정확히 교체한다. §A.1 의 첫 줄은 `## 2. 해외주식/미국주식 계좌` 헤딩 자체로 시작하고, 마지막 줄 뒤에 빈 줄 1 개를 둔다 (다음 헤딩 `## 3.` 앞 공백).

### 3.2 §4 본문 교체

같은 파일 안에서 `## 4. 모의투자 주문` 헤딩부터 그 섹션이 끝나는 `## 다음 작업 가이드` 헤딩 **직전**까지의 모든 줄을 §A.2 본문으로 정확히 교체한다. §A.2 의 첫 줄은 `## 4. 모의투자 주문` 헤딩 자체로 시작하고, 마지막 줄 뒤에 빈 줄 1 개를 둔다.

### 3.3 patch.md 작성

`projects/paper-trading/docs/ai/jobs/KIS_2/patch.md` 를 §A.3 의 양식 그대로 작성한다. Codex 가 실행한 검증 결과 (`compileall` 출력, 안전 grep 결과) 만 채워 넣는다.

### 3.4 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
```

OK 여야 한다 (코드 무변경 회귀).

안전 grep (모두 0 줄이어야 함):

```bash
grep -n "Bearer eyJ\|appkey=\|appsecret=\|access_token=" /root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md
grep -n "12345678\|fake-key\|fake-secret" /root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md
grep -nE "import (requests|httpx|aiohttp|urllib3)" /root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md
```

diff 확인:

```bash
git diff -- /root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md
```

§2 와 §4 외 다른 섹션 (§1 OAuth / §3 시세 / 정책 / 다음 작업 가이드 / 보안) 의 변동 줄 0 이어야 한다.

`pytest -p no:cacheprovider` 실행은 선택. 실행한다면 기존 통과 수와 동일해야 한다 (코드 무변경).

---

## §A. byte-level 본문 (전면 교체용)

### §A.1 — `## 2. 해외주식/미국주식 계좌` 본문 (전면 교체)

다음 본문을 `docs/kis/MISSING_OFFICIAL_VALUES.md` 의 §2 자리에 byte-level 그대로 적용한다. 본문 자체에 줄을 추가/수정/삭제 금지.

```markdown
## 2. 해외주식/미국주식 계좌

본 섹션은 KIS Developers 공식 자료 (2026-05-19 사용자 업로드 `uploads/6.xlsx`) 에서 직접 확인된 해외주식 계좌·잔고·증거금 endpoint catalog 입니다. `Confirmed: yes` 항목은 6.xlsx 에 명시된 값에 한정하며, 그 외는 `<TBD>` 와 `Confirmed: no` 로 유지합니다. 실 app key / app secret / 계좌번호 / access token 은 본 catalog 에 절대 기록하지 않습니다.

### 2.1 공통 base URL

| 환경 | Base URL | Confirmed |
| --- | --- | --- |
| 실전 | `https://openapi.koreainvestment.com:9443` | yes |
| 모의 | `https://openapivts.koreainvestment.com:29443` | yes |

### 2.2 endpoint catalog

| 메뉴 | path | HTTP method | 실전 TR_ID | 모의 TR_ID | Confirmed |
| --- | --- | --- | --- | --- | --- |
| 해외주식 잔고 | `/uapi/overseas-stock/v1/trading/inquire-balance` | GET | `TTTS3012R` | `VTTS3012R` | yes |
| 해외주식 매수가능금액조회 | `/uapi/overseas-stock/v1/trading/inquire-psamount` | GET | `TTTS3007R` | `VTTS3007R` | yes |
| 해외주식 체결기준현재잔고 | `/uapi/overseas-stock/v1/trading/inquire-present-balance` | GET | `CTRP6504R` | `VTRP6504R` (모의는 output3만 사용 가능) | yes |
| 해외주식 결제기준잔고 | `/uapi/overseas-stock/v1/trading/inquire-paymt-stdr-balance` | GET | `CTRP6010R` | 모의투자 미지원 | yes |
| 해외주식 일별거래내역 | `/uapi/overseas-stock/v1/trading/inquire-period-trans` | GET | `CTOS4001R` | 모의투자 미지원 | yes |
| 해외주식 기간손익 | `/uapi/overseas-stock/v1/trading/inquire-period-profit` | GET | `TTTS3039R` | 모의투자 미지원 | yes |
| 해외증거금 통화별조회 | `/uapi/overseas-stock/v1/trading/foreign-margin` | GET | `TTTC2101R` | 모의투자 미지원 | yes |

### 2.3 공통 Request Header

본 표는 6.xlsx 의 endpoint sheet (잔고 / 매수가능금액조회 / 체결기준현재잔고 등) 에서 모두 동일하게 명시된 헤더 골격입니다.

| Header | 필수 | 값/형식 | Confirmed |
| --- | --- | --- | --- |
| `content-type` | 응답 측 필수, 요청 측 옵션 | `application/json; charset=utf-8` | yes |
| `authorization` | Y | `Bearer ${access_token}` (OAuth `/oauth2/tokenP` 발급) | yes |
| `appkey` | Y | 한국투자증권에서 발급, length 36 | yes |
| `appsecret` | Y | 한국투자증권에서 발급, length 180 | yes |
| `personalseckey` | N (법인 필수) | 제휴사 회원 관리용 고객식별키 | yes |
| `tr_id` | Y | 위 2.2 의 endpoint 별 TR_ID | yes |
| `tr_cont` | N | 공백: 초기 조회, `N`: 다음 데이터 조회 (지원 endpoint 에 한해 — 잔고 / 주문체결내역 / 체결기준 현재잔고 등) | yes |
| `custtype` | N | `B`(법인) / `P`(개인) | yes |
| `seq_no`, `mac_address`, `phone_number`, `ip_addr`, `gt_uid` | 대부분 옵션 (일부 법인 필수) | 본 저장소는 개인 사용자 가정으로 미설정 | yes |

### 2.4 endpoint 별 Request query/body 핵심 필드

| Endpoint | Field | 필수 | 의미 / 모의 제약 | Confirmed |
| --- | --- | --- | --- | --- |
| 잔고 (`VTTS3012R`) | `CANO` | Y | 종합계좌번호 앞 8자리 | yes |
| 잔고 | `ACNT_PRDT_CD` | Y | 계좌상품코드 뒤 2자리 | yes |
| 잔고 | `OVRS_EXCG_CD` | Y | 모의: `NASD`/`NYSE`/`AMEX` 만 허용 (실전은 `NASD`=미국전체 등 다양) | yes |
| 잔고 | `TR_CRCY_CD` | Y | `USD`/`HKD`/`CNY`/`JPY`/`VND` | yes |
| 잔고 | `CTX_AREA_FK200`, `CTX_AREA_NK200` | N | 페이지네이션 연속조회 키 (공란이면 최초 조회) | yes |
| 매수가능금액 (`VTTS3007R`) | `CANO` / `ACNT_PRDT_CD` / `OVRS_EXCG_CD` / `OVRS_ORD_UNPR` / `ITEM_CD` | Y | 종목별 매수 가능 금액·수량 조회 | yes |
| 체결기준 현재잔고 (`VTRP6504R`) | `CANO` / `ACNT_PRDT_CD` | Y | 종합계좌번호 + 상품코드 | yes |
| 체결기준 현재잔고 | `WCRC_FRCR_DVSN_CD` | Y | `01`=원화, `02`=외화 | yes |
| 체결기준 현재잔고 | `NATN_CD` | Y | `000`=전체, `840`=미국, `344`=홍콩, `156`=중국, `392`=일본, `704`=베트남 | yes |
| 체결기준 현재잔고 | `TR_MKET_CD` | Y | NATN_CD 별 거래시장 코드 | yes |
| 체결기준 현재잔고 | `INQR_DVSN_CD` | Y | `00`=전체, `01`=일반해외주식, `02`=미니스탁 | yes |

### 2.5 endpoint 별 Response body 핵심 필드

| Endpoint | Field | Type | 의미 | Confirmed |
| --- | --- | --- | --- | --- |
| 공통 | `rt_cd` | string | `0`=성공, 그 외=실패 | yes |
| 공통 | `msg_cd` | string | 응답코드 | yes |
| 공통 | `msg1` | string | 응답메시지 | yes |
| 잔고 | `output1[]` | array | 포지션 list | yes |
| 잔고 | `output1[].ovrs_pdno` | string | 해외상품번호 (symbol) | yes |
| 잔고 | `output1[].ovrs_item_name` | string | 해외종목명 | yes |
| 잔고 | `output1[].ovrs_cblc_qty` | string | 해외잔고수량 | yes |
| 잔고 | `output1[].ord_psbl_qty` | string | 매도 가능 수량 | yes |
| 잔고 | `output1[].pchs_avg_pric` | string | 매입평균가격 | yes |
| 잔고 | `output1[].frcr_pchs_amt1` | string | 외화매입금액 | yes |
| 잔고 | `output1[].ovrs_stck_evlu_amt` | string | 외화평가금액 | yes |
| 잔고 | `output1[].now_pric2` | string | 현재가 | yes |
| 잔고 | `output1[].frcr_evlu_pfls_amt` | string | 외화평가손익금액 | yes |
| 잔고 | `output1[].evlu_pfls_rt` | string | 평가손익율 | yes |
| 잔고 | `output1[].tr_crcy_cd` | string | 거래통화코드 (`USD`/`HKD`/...) | yes |
| 잔고 | `output1[].ovrs_excg_cd` | string | 해외거래소코드 | yes |
| 잔고 | `output2` | object | 계좌 집계 (총평가손익 / 총수익률 등) | yes |
| 잔고 | `output2.tot_evlu_pfls_amt` | string | 총평가손익금액 | yes |
| 잔고 | `output2.tot_pftrt` | string | 총수익률 | yes |
| 잔고 | `output2.ovrs_tot_pfls` | string | 해외총손익 | yes |
| 잔고 | `ctx_area_fk200` / `ctx_area_nk200` | string | 다음페이지 연속조회 키 | yes |
| 매수가능금액 | `output.tr_crcy_cd` | string | 거래통화코드 | yes |
| 매수가능금액 | `output.ord_psbl_frcr_amt` | string | 주문가능외화금액 | yes |
| 매수가능금액 | `output.ovrs_ord_psbl_amt` | string | 해외주문가능금액 ("외화" 모드) | yes |
| 매수가능금액 | `output.max_ord_psbl_qty` | string | 최대주문가능수량 ("외화" 모드) | yes |
| 매수가능금액 | `output.frcr_ord_psbl_amt1` | string | 외화주문가능금액1 ("통합" 모드) | yes |
| 매수가능금액 | `output.ovrs_max_ord_psbl_qty` | string | 해외최대주문가능수량 ("통합" 모드) | yes |
| 매수가능금액 | `output.exrt` | string | 환율 — **본 저장소는 FX 변환을 도입하지 않으므로 표시 목적으로만 사용** | yes |
| 체결기준 현재잔고 | `output3` (모의) | object | 모의에서 유일하게 사용 가능한 응답 필드. 종목 / 통화 / 합산 정보 일부. 모의 사용 시 `output1`/`output2` 미사용 | yes |

### 2.6 모의투자 제약사항

- 모의투자에서 `OVRS_EXCG_CD` 는 `NASD` / `NYSE` / `AMEX` 만 사용 (잔고 sheet 명시). 실전은 `NASD`=미국전체 + `SEHK` / `SHAA` / `SZAA` / `TKSE` / `HASE` / `VNSE` 등 다양.
- 모의투자에서 `TR_CRCY_CD` 는 `USD` / `HKD` / `CNY` / `JPY` / `VND` 가 공식 명시 (잔고 sheet).
- **체결기준 현재잔고는 모의에서 `output3` 만 사용 가능** (API 목록 sheet `https://openapivts.koreainvestment.com:29443    (output3만 이용 가능)`).
- **결제기준 잔고 (`CTRP6010R`) / 일별거래내역 (`CTOS4001R`) / 기간손익 (`TTTS3039R`) / 해외증거금 통화별 (`TTTC2101R`) 은 모의투자 미지원**.
- 모의투자 자체가 일부 종목에 한해서만 매매 가능하다는 KIS 공식 안내가 있음 (주문 sheet 개요 명시). 본 catalog 는 종목 단위 정확한 list 를 보유하지 않으며, 매매 종목 list 는 후속 별 job 에서 확인 필요. (`<TBD>`)
- `app/portfolio/account.py` 의 currency-별 cash ledger 와 `PortfolioService` 의 통화별 PnL 분리는 본 catalog 와 정합. **FX 변환 함수 / 환율 상수 / base currency 통합 함수 도입 금지** 정책 유지.

```

(위 본문에는 `output3` 의 상세 sub-field list 는 포함하지 않습니다. 모의 환경에서 본 저장소가 우선 매핑할 항목은 잔고 (`VTTS3012R`) 와 매수가능금액 (`VTTS3007R`) 이며, `output3` 의 sub-field 는 후속 job 에서 추가 catalog 화합니다. `<TBD>` 마커는 의도적입니다.)

### §A.2 — `## 4. 모의투자 주문` 본문 (전면 교체)

다음 본문을 `docs/kis/MISSING_OFFICIAL_VALUES.md` 의 §4 자리에 byte-level 그대로 적용한다. 본문 자체에 줄을 추가/수정/삭제 금지.

```markdown
## 4. 모의투자 주문

본 섹션은 KIS Developers 공식 자료 (2026-05-19 사용자 업로드 `uploads/6.xlsx`) 에서 직접 확인된 해외주식 주문·정정·취소·예약·체결 endpoint catalog 입니다. `Confirmed: yes` 항목은 6.xlsx 에 명시된 값에 한정합니다. **실주문 HTTP 구현은 본 catalog 가 충족된 뒤에도 별 job 에서 `KIS_ORDER_DRY_RUN=true` 기본값 + `validate_kis_order_request` pre-flight 를 유지한 채 단계적으로 연결합니다.**

### 4.1 공통 base URL

§2.1 과 동일.

| 환경 | Base URL | Confirmed |
| --- | --- | --- |
| 실전 | `https://openapi.koreainvestment.com:9443` | yes |
| 모의 | `https://openapivts.koreainvestment.com:29443` | yes |

### 4.2 endpoint catalog

| 메뉴 | path | HTTP method | 실전 TR_ID | 모의 TR_ID | Confirmed |
| --- | --- | --- | --- | --- | --- |
| 해외주식 주문 | `/uapi/overseas-stock/v1/trading/order` | POST | 미국매수 `TTTT1002U`, 미국매도 `TTTT1006U`, 홍콩 매수 `TTTS1002U`, 홍콩 매도 `TTTS1001U`, 일본 매수 `TTTS0308U`, 일본 매도 `TTTS0307U` (그 외 아시아는 6.xlsx 주문 sheet `tr_id` 셀 본문 참조) | 미국매수 `VTTT1002U`, 미국매도 `VTTT1001U` (아시아 모의 TR_ID 는 주문 sheet `tr_id` 셀 본문 참조) | yes |
| 해외주식 정정취소주문 | `/uapi/overseas-stock/v1/trading/order-rvsecncl` | POST | 미국 `TTTT1004U`, 홍콩 `TTTS1003U`, 일본 `TTTS0309U` (그 외 아시아는 정정취소 sheet `tr_id` 셀 본문 참조) | 미국 `VTTT1004U` (그 외 아시아는 정정취소 sheet `tr_id` 셀 본문 참조) | yes |
| 해외주식 예약주문접수 | `/uapi/overseas-stock/v1/trading/order-resv` | POST | 미국 예약 매수 `TTTT3014U`, 미국 예약 매도 `TTTT3016U`, 중국/홍콩/일본/베트남 예약 `TTTS3013U` | 미국 예약 매수 `VTTT3014U`, 미국 예약 매도 `VTTT3016U`, 중국/홍콩/일본/베트남 예약 `VTTS3013U` | yes |
| 해외주식 예약주문접수취소 | `/uapi/overseas-stock/v1/trading/order-resv-ccnl` | POST | 미국 예약 취소 `TTTT3017U` (아시아 미제공) | 미국 예약 취소 `VTTT3017U` (아시아 미제공) | yes |
| 해외주식 미체결내역 | `/uapi/overseas-stock/v1/trading/inquire-nccs` | GET | `TTTS3018R` | 모의투자 미지원 | yes |
| 해외주식 주문체결내역 | `/uapi/overseas-stock/v1/trading/inquire-ccnl` | GET | `TTTS3035R` | `VTTS3035R` (모의 제약 §4.7 참조) | yes |
| 해외주식 예약주문조회 | `/uapi/overseas-stock/v1/trading/order-resv-list` | GET | 미국 `TTTT3039R`, 일본/중국/홍콩/베트남 `TTTS3014R` | 모의투자 미지원 | yes |
| 해외주식 미국주간주문 | `/uapi/overseas-stock/v1/trading/daytime-order` | POST | 주간매수 `TTTS6036U`, 주간매도 `TTTS6037U` | 모의투자 미지원 | yes |
| 해외주식 미국주간정정취소 | `/uapi/overseas-stock/v1/trading/daytime-order-rvsecncl` | POST | `TTTS6038U` | 모의투자 미지원 | yes |
| 해외주식 지정가주문번호조회 | `/uapi/overseas-stock/v1/trading/algo-ordno` | GET | `TTTS6058R` | 모의투자 미지원 | yes |
| 해외주식 지정가체결내역조회 | `/uapi/overseas-stock/v1/trading/inquire-algo-ccnl` | GET | `TTTS6059R` | 모의투자 미지원 | yes |

### 4.3 공통 Request Header

§2.3 과 동일 (content-type / authorization / appkey / appsecret / personalseckey / tr_id / tr_cont / custtype / seq_no / mac_address / phone_number / ip_addr / gt_uid).

### 4.4 주문 (POST `/order`) Request Body 핵심 필드

| Field | 필수 | 의미 / 모의 제약 | Confirmed |
| --- | --- | --- | --- |
| `CANO` | Y | 종합계좌번호 앞 8자리 | yes |
| `ACNT_PRDT_CD` | Y | 계좌상품코드 뒤 2자리 | yes |
| `OVRS_EXCG_CD` | Y | `NASD` 나스닥 / `NYSE` 뉴욕 / `AMEX` 아멕스 / `SEHK` 홍콩 / `SHAA` 중국상해 / `SZAA` 중국심천 / `TKSE` 일본 / `HASE` 베트남 하노이 / `VNSE` 베트남 호치민 (모의는 미국 3 거래소만 검증됨) | yes |
| `PDNO` | Y | 종목코드 | yes |
| `ORD_QTY` | Y | 주문수량 (거래소별 최소 주문수량/단위 확인 필요) | yes |
| `OVRS_ORD_UNPR` | Y | 1주당 가격. **시장가의 경우 1주당 가격을 공란이 아닌 `"0"` 으로 입력** (단 모의에서는 시장가 미지원, §4.7 참조) | yes |
| `ORD_DVSN` | Y | 주문구분. **모의 (`VTTT1002U` 미국매수 / `VTTT1006U` 미국매도 / `VTTS1001U` 홍콩매도 등) 는 `00` 지정가만 가능**. 실전 미국매수: `00` 지정가, `32` LOO, `34` LOC, `35` TWAP, `36` VWAP. 실전 미국매도: `00`, `31` MOO, `32` LOO, `33` MOC, `34` LOC, `35` TWAP, `36` VWAP. 홍콩 매도 추가: `50` 단주지정가. TWAP/VWAP 정정 불가 | yes |
| `ORD_SVR_DVSN_CD` | Y | `"0"` (Default) | yes |
| `CTAC_TLNO` | N | 연락전화번호 | yes |
| `MGCO_APTM_ODNO` | N | 운용사지정주문번호 | yes |
| `SLL_TYPE` | N | 제거=매수, `00`=매도 | yes |
| `START_TIME` / `END_TIME` / `ALGO_ORD_TMD_DVSN_CD` | N | TWAP/VWAP 분할주문 시간만 사용 (모의 미지원) | yes |

### 4.5 주문 Response Body 핵심 필드

| Field | Type | 의미 | Confirmed |
| --- | --- | --- | --- |
| `rt_cd` | string | `0`=성공, 그 외=실패 | yes |
| `msg_cd` | string | 응답코드 | yes |
| `msg1` | string | 응답메시지 | yes |
| `output.KRX_FWDG_ORD_ORGNO` | string (5) | 한국투자증권 시스템 지정 영업점코드 | yes |
| `output.ODNO` | string (10) | 주문번호 — broker_order_id 후보 | yes |
| `output.ORD_TMD` | string (6) | 주문시각 `HHMMSS` | yes |

### 4.6 정정취소 (POST `/order-rvsecncl`) Request Body 핵심 필드

| Field | 필수 | 의미 | Confirmed |
| --- | --- | --- | --- |
| `CANO` / `ACNT_PRDT_CD` / `OVRS_EXCG_CD` / `PDNO` | Y | 계좌 / 거래소 / 종목 | yes |
| `ORGN_ODNO` | Y | 원주문번호 (`/order` 응답의 `ODNO`, 또는 미체결 조회의 `odno`) | yes |
| `RVSE_CNCL_DVSN_CD` | Y | `01`=정정, `02`=취소 | yes |
| `ORD_QTY` | Y | 주문수량 | yes |
| `OVRS_ORD_UNPR` | Y | 정정 단가. **취소주문 시 `"0"` 입력** | yes |
| `MGCO_APTM_ODNO` / `ORD_SVR_DVSN_CD` | N | 운용사지정주문번호 / 주문서버구분코드 | yes |

정정취소 Response Body 핵심: `rt_cd` / `msg_cd` / `msg1` + `output.KRX_FWDG_ORD_ORGNO` / `output.ODNO` / `output.ORD_TMD` (주문 응답과 동일 형태).

### 4.7 주문체결내역 (`VTTS3035R`) 모의 제약

GET `/uapi/overseas-stock/v1/trading/inquire-ccnl` 의 Request Query Parameter 는 다음과 같다. 모의 제약 (6.xlsx 주문체결내역 sheet 명시) 을 별도 표시한다.

| Field | 필수 | 의미 | 모의 제약 | Confirmed |
| --- | --- | --- | --- | --- |
| `CANO` / `ACNT_PRDT_CD` | Y | 계좌 | — | yes |
| `PDNO` | Y | 종목코드 | 모의는 `""` (전체 조회) 만 가능 | yes |
| `ORD_STRT_DT` / `ORD_END_DT` | Y | 주문 기간 (YYYYMMDD, 현지시각 기준) | — | yes |
| `SLL_BUY_DVSN` | Y | `00`=전체, `01`=매도, `02`=매수 | 모의는 `"00"` 만 | yes |
| `CCLD_NCCS_DVSN` | Y | `00`=전체, `01`=체결, `02`=미체결 | 모의는 `"00"` 만 | yes |
| `OVRS_EXCG_CD` | Y | 거래소 코드 (`%`=전체, `NASD`=미국전체 등) | 모의는 §4.4 의 거래소 제약 따름 | yes |
| `SORT_SQN` | Y | `DS`=정순, `AS`=역순 | 모의는 정렬 순서 사용 불가 (Default `DS`) | yes |
| `ORD_DT` / `ORD_GNO_BRNO` / `ODNO` | Y | `""` Null | 주문번호 검색 불가, 반드시 `""` | yes |
| `CTX_AREA_NK200` / `CTX_AREA_FK200` | Y | 연속조회 키 | — | yes |

주문체결내역 Response Body: `rt_cd` / `msg_cd` / `msg1` + `output[]` array (체결/미체결 항목). 본 catalog 는 array 의 sub-field full list 를 보유하지 않으며, 매핑 단계의 별 job 에서 6.xlsx 주문체결내역 sheet 의 sub-field 표를 추가 catalog 화한다. (`<TBD>`)

### 4.8 모의투자 미지원 endpoint 목록

다음 endpoint 들은 6.xlsx API 목록 sheet 에서 **"모의투자 미지원"** 으로 명시되어 있다. 본 저장소의 `KisBroker` 는 이 endpoint 들에 대해 `NotImplementedError` 를 raise 유지한다.

- 해외주식 미체결내역 (`TTTS3018R`)
- 해외주식 예약주문조회 (미국 `TTTT3039R`, 아시아 `TTTS3014R`)
- 해외주식 결제기준잔고 (`CTRP6010R`)
- 해외주식 일별거래내역 (`CTOS4001R`)
- 해외주식 기간손익 (`TTTS3039R`)
- 해외증거금 통화별조회 (`TTTC2101R`)
- 해외주식 미국주간주문 (`TTTS6036U` / `TTTS6037U`)
- 해외주식 미국주간정정취소 (`TTTS6038U`)
- 해외주식 지정가주문번호조회 (`TTTS6058R`)
- 해외주식 지정가체결내역조회 (`TTTS6059R`)

### 4.9 모의투자 주문 유형 / 거래소 / 통화 제약 요약

- 주문구분 (`ORD_DVSN`): **모의투자는 `00` 지정가 (LIMIT) 만 사용 가능**. 시장가 / LOO / LOC / MOO / MOC / TWAP / VWAP 모두 미지원. 본 저장소의 `OrderType.MARKET` 3중 가드 (`allow_paper_market_orders=False` 기본 + `TradingMode.PAPER` + `live_trading_enabled=False`) 가 이 정책과 정합.
- 거래소 (`OVRS_EXCG_CD`): 모의 잔고 sheet 기준 `NASD` / `NYSE` / `AMEX` 명시. 그 외 아시아 거래소 모의 지원 여부는 endpoint 별로 6.xlsx 의 모의 TR_ID 칸을 참조.
- 통화 (`TR_CRCY_CD`): `USD` / `HKD` / `CNY` / `JPY` / `VND` (잔고 sheet). 본 저장소는 통화별 분리 보고 정책을 유지하고 FX 변환을 도입하지 않는다.
- 모의에서 일부 종목만 매매 가능 (주문 sheet 개요). 종목 list 는 본 catalog 의 `<TBD>` 로 남기며, 매매 가능 종목 확인은 별 job 또는 KIS 포털 통해 수행.

### 4.10 안전 정책 재확인

- 모든 주문은 Strategy → RiskEngine → OMS → PaperBroker / KisBroker 경로를 통과해야 한다. catalog 가 채워졌어도 OMS / RiskEngine 우회는 금지.
- 실주문 HTTP 연결은 `KIS_ORDER_DRY_RUN=true` 기본값 + `validate_kis_order_request` pre-flight + `ALLOW_MARKET_ORDERS=true` 차단을 유지한 채 단계적으로 활성화한다.
- `app key`, `app secret`, `계좌번호`, `access_token`, `Bearer` 토큰 원문은 본 catalog 와 코드 / 응답 / 로그 어디에도 기록하지 않는다.
- LLM / Agent 는 `OrderIntent` 같은 non-executable intent 까지만 만들 수 있다. executable `BrokerOrder` / `Order` 생성은 OMS 만 수행한다.

```

### §A.3 — `patch.md` 양식

`projects/paper-trading/docs/ai/jobs/KIS_2/patch.md` 를 다음 본문 그대로 작성한다. Codex 가 직접 확인한 검증 결과만 채워 넣는다.

```markdown
# KIS_2 — Codex 구현 요약

## 변경된 파일

- `docs/kis/MISSING_OFFICIAL_VALUES.md` (§2 와 §4 본문 교체)
- `projects/paper-trading/docs/ai/jobs/KIS_2/patch.md` (본 파일)

Pre-existing unrelated dirty files were left untouched.

## 채워진 값 — §2 해외주식 계좌

Paper-지원 endpoint 4 종:

- 해외주식 잔고 `VTTS3012R` (`/inquire-balance`)
- 해외주식 매수가능금액 `VTTS3007R` (`/inquire-psamount`)
- 해외주식 체결기준 현재잔고 `VTRP6504R` (`/inquire-present-balance`, 모의는 `output3` 만 사용 가능)

Paper-미지원 endpoint 4 종 (실전 TR_ID 만 명시):

- 해외주식 결제기준 잔고 `CTRP6010R`
- 해외주식 일별거래내역 `CTOS4001R`
- 해외주식 기간손익 `TTTS3039R`
- 해외증거금 통화별조회 `TTTC2101R`

공통 헤더 / 거래소 (모의: NASD/NYSE/AMEX) / 통화 (USD/HKD/CNY/JPY/VND) 정리 완료. 잔고 응답의 `output1[]` (포지션) / `output2` (계좌 집계) 핵심 필드와 매수가능금액 응답의 `output` 핵심 필드를 catalog 화.

## 채워진 값 — §4 모의투자 주문

Paper-지원 endpoint 5 종:

- 해외주식 주문 `VTTT1002U` (미국 매수) / `VTTT1001U` (미국 매도) (`/order`)
- 해외주식 정정취소주문 `VTTT1004U` (미국 정정·취소) (`/order-rvsecncl`)
- 해외주식 예약주문 접수 `VTTT3014U` / `VTTT3016U` (미국) / `VTTS3013U` (아시아) (`/order-resv`)
- 해외주식 예약주문 취소 `VTTT3017U` (미국만) (`/order-resv-ccnl`)
- 해외주식 주문체결내역 `VTTS3035R` (`/inquire-ccnl`, 모의 제약 다수)

Paper-미지원 endpoint 6 종 (실전 TR_ID 만 명시):

- 해외주식 미체결내역 `TTTS3018R` (`/inquire-nccs`)
- 해외주식 예약주문조회 `TTTT3039R` / `TTTS3014R` (`/order-resv-list`)
- 해외주식 미국주간주문 `TTTS6036U` / `TTTS6037U` (`/daytime-order`)
- 해외주식 미국주간정정취소 `TTTS6038U` (`/daytime-order-rvsecncl`)
- 해외주식 지정가주문번호조회 `TTTS6058R`
- 해외주식 지정가체결내역조회 `TTTS6059R`

핵심 결론: **모의투자는 `ORD_DVSN=00` 지정가 (LIMIT) 만 지원**. 시장가 / LOO / LOC / MOO / MOC / TWAP / VWAP 모두 모의 미지원. 본 저장소의 `OrderType.MARKET` 3중 가드 정책과 일치.

## 부족한 값 (`<TBD>` 로 남긴 항목)

- 모의에서 매매 가능한 정확한 종목 list (주문 sheet 개요만 "일부 종목" 명시, 종목 list 부재).
- 체결기준 현재잔고 `output3` 의 sub-field 상세 (모의에서 사용 가능한 유일한 응답이지만 sub-field 표는 별 job 으로 catalog 화 권장).
- 주문체결내역 `output[]` array sub-field 상세.
- 아시아 거래소 (`SEHK`/`SHAA`/`SZAA`/`TKSE`/`HASE`/`VNSE`) 의 모의 TR_ID full list (6.xlsx 주문 sheet `tr_id` 셀 본문에 일부 명시되어 있으나 본 catalog 는 미국 + 대표 아시아만 표시. 필요시 별 job 으로 보강).

## 안전 회귀 확인

- 코드 / 테스트 변경 0건. 
- `python -m compileall app tests` 통과.
- 안전 grep clean:
  - `Bearer eyJ` / `appkey=` / `appsecret=` / `access_token=` 등 자격증명 패턴 0 줄.
  - `12345678` / `fake-key` / `fake-secret` 등 fixture 잔재 0 줄.
  - `import requests` / `httpx` / `aiohttp` / `urllib3` 0 줄.
- `MISSING_MARKET_DATA_VALUES.md` 무변동.
- §1 OAuth / §3 시세 / 정책 / 다음 작업 가이드 / 보안 섹션 무변동.
- `OrderType.MARKET` 가드 / live trading 가드 / RiskEngine / OMS / PaperBroker / KIS adapter 정책 변동 0건.
- 자동 git commit / push / merge / deploy 수행 안 함.

## 다음 작업 진행 가능 여부 판단

- **`api-account-001` (해외주식 계좌 / 잔고 / 매수가능금액 / 체결기준 현재잔고 paper HTTP 연결)**: 진행 가능. 잔고 (`VTTS3012R`) 와 매수가능금액 (`VTTS3007R`) 의 endpoint / TR ID / headers / request fields / response fields 가 모두 `Confirmed: yes`. 체결기준 현재잔고 (`VTRP6504R`) 는 모의 `output3` 한정이라 부분 구현 가능. 후속 job 은 §2 의 catalog 만 참고하고 추측 금지.
- **`api-orders-paper-001` (해외주식 모의 주문 / 정정·취소 paper HTTP 연결)**: 진행 가능. 주문 (`VTTT1002U` 미국매수 / `VTTT1001U` 미국매도) 과 정정취소 (`VTTT1004U`) 의 endpoint / TR ID / headers / request body fields / response body fields 가 모두 `Confirmed: yes`. **단 LIMIT 만 허용** — 본 저장소의 `OrderType.MARKET` 3중 가드를 그대로 유지하고 `ORD_DVSN=00` 만 송신한다. `KIS_ORDER_DRY_RUN=true` 기본값 + `validate_kis_order_request` pre-flight + OMS 단독 executable order 생성 + Strategy/Agent 의 broker 직접 호출 금지 정책 그대로.
- 미체결 (`TTTS3018R`) / 예약주문조회 / 미국주간 / 지정가주문번호·체결내역 endpoint 는 모의 미지원이므로 paper 단계에서는 `NotImplementedError` 유지.

READY FOR REVIEW
```

## 4. 자가 점검 (구현 후)

- [ ] `docs/kis/MISSING_OFFICIAL_VALUES.md` §2 와 §4 본문만 변경됐다. 다른 섹션 변동 0 줄 (`git diff` 검증).
- [ ] `docs/kis/MISSING_MARKET_DATA_VALUES.md` 변경 0 줄.
- [ ] `app/`, `tests/`, `.env*`, `pyproject.toml`, `pytest.ini`, `README.md`, `app/api/*`, `app/static/*`, `app/main.py`, `app/config.py`, `app/broker/*`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/strategy/*`, `app/session/*`, `app/runtime/*` 변경 0 건.
- [ ] catalog 본문에 실 app key / app secret / 계좌번호 / Bearer / refresh token / access token 등장 0 회. `Bearer ${access_token}` placeholder 만 허용.
- [ ] `python -m compileall app tests` 통과.
- [ ] 안전 grep (Bearer eyJ / appkey= / appsecret= / access_token= / fake-key / fake-secret / 12345678 / import requests 등) 모두 0 줄.
- [ ] `patch.md` 가 §A.3 양식 그대로 (변경 파일 / 채운 값 / 부족한 값 / 안전 회귀 / 다음 작업 가능 여부) 포함.
- [ ] commit / push / merge / deploy 를 너가 직접 실행하지 않았다.

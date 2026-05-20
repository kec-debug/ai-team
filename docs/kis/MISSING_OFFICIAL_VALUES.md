# KIS Open API - Missing Official Values

본 문서는 KIS Open API 모의투자 HTTP 연결을 구현하기 위해 필요한 공식 문서값의 갭을 정리합니다. 본 저장소는 KIS endpoint, TR ID, header, payload를 추측하지 않습니다. 아래 항목이 KIS 공식 Open API 문서에서 확인된 뒤에만 별도 mvp에서 HTTP 연결을 진행합니다.

## 정책

- 본 표의 모든 `<TBD>` 항목은 KIS 공식 Open API 개발자 포털 문서에서 직접 확인해 채워 넣어야 합니다.
- 실전투자(live) endpoint는 본 저장소에 추가하지 않습니다. 모의투자(paper) endpoint만 다룹니다.
- 실제 app key, app secret, 계좌번호, access token 값은 본 문서/저장소 어디에도 기록하지 않습니다.
- 항목별로 `Confirmed: no`인 한 해당 HTTP 기능은 `NotImplementedError` 또는 dry-run 상태를 유지합니다.

## 1. OAuth 인증

| 항목 | 설명 | 값 | Confirmed |
| --- | --- | --- | --- |
| Paper trading base URL | 모의투자 환경 base URL | `<TBD>` | no |
| OAuth token endpoint | 토큰 발급 path | `<TBD>` | no |
| OAuth token HTTP method | `POST`/`GET` 등 | `<TBD>` | no |
| Token refresh endpoint (있으면) | 갱신 path | `<TBD>` | no |
| Required request headers | `content-type` 등 | `<TBD>` | no |
| Request body fields | `grant_type`, `appkey`, `appsecret`, ... | `<TBD>` | no |
| Response token field name | `access_token`/`token` 등 | `<TBD>` | no |
| Response token expiry field | `expires_in`/`expires_at` 등 | `<TBD>` | no |
| Token type field (있으면) | `Bearer` 등 | `<TBD>` | no |

충족 시 후속 mvp가 `KisAuthClient.authenticate()` / `refresh_token()`을 실제 HTTP로 연결합니다.

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

## 3. 해외주식/미국주식 시세

| 항목 | 설명 | 값 | Confirmed |
| --- | --- | --- | --- |
| 해외주식 현재가 endpoint | path | `<TBD>` | no |
| 해외주식 현재가 TR ID | 모의투자용 TR ID(시세는 실전과 공유될 수 있음 - 공식 문서 확인 필요) | `<TBD>` | no |
| Request fields | 종목코드, 거래소 코드 등 | `<TBD>` | no |
| Response bid/ask/last 필드 | `<TBD>` | `<TBD>` | no |
| Response quote timestamp 필드 | `<TBD>` | `<TBD>` | no |
| Stale quote 판단 기준 | 초/밀리초 등 단위 | `<TBD>` | no |

충족 시 후속 mvp가 `KisMarketDataClient.get_quote()` / `get_last_price()`를 실제 HTTP로 연결합니다.

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

### 4.7.1 주문체결내역 (`VTTS3035R`) Response `output[]` sub-fields

본 표는 `uploads/6.xlsx` 의 **`해외주식 주문체결내역`** sheet 에서 직접 추출한 응답 sub-field 정의이다. `Confirmed: yes` 행은 6.xlsx 셀 본문에 명시된 값에 한정한다. 모의 제약은 sheet 에 명시된 경우에만 별도 표기한다. 본 catalog 는 paper (`VTTS3035R`) 와 실전 (`TTTS3035R`) 공통 응답을 다루며, 모의 제약은 §4.7 의 request 측 제약과 함께 해석한다.

| Field | Type | 의미 | 모의 제약 | Confirmed |
| --- | --- | --- | --- | --- |
| `output[].ord_dt` | string (8) | 주문일자 — 주문접수 일자 (현지시각 기준) | — | yes |
| `output[].ord_gno_brno` | string (5) | 주문채번지점번호 — 계좌 개설 시 관리점으로 선택한 영업점의 고유번호 | — | yes |
| `output[].odno` | string (10) | 주문번호 — 접수한 주문의 일련번호. 정정취소주문 시 해당 값 `odno` 사용 | — | yes |
| `output[].orgn_odno` | string (10) | 원주문번호 — 정정 또는 취소 대상 주문의 일련번호 | — | yes |
| `output[].sll_buy_dvsn_cd` | string (2) | 매도매수구분코드 — `01`=매도, `02`=매수 | — | yes |
| `output[].sll_buy_dvsn_cd_name` | string (60) | 매도매수구분코드명 | — | yes |
| `output[].rvse_cncl_dvsn` | string (2) | 정정취소구분 — `01`=정정, `02`=취소 | — | yes |
| `output[].rvse_cncl_dvsn_name` | string (60) | 정정취소구분명 | — | yes |
| `output[].pdno` | string (12) | 상품번호 | — | yes |
| `output[].prdt_name` | string (60) | 상품명 | — | yes |
| `output[].ft_ord_qty` | string (10) | FT주문수량 — 주문수량 | — | yes |
| `output[].ft_ord_unpr3` | string (26) | FT주문단가3 — 주문가격 | — | yes |
| `output[].ft_ccld_qty` | string (10) | FT체결수량 — 체결된 수량 | — | yes |
| `output[].ft_ccld_unpr3` | string (26) | FT체결단가3 — 체결된 가격 | — | yes |
| `output[].ft_ccld_amt3` | string (23) | FT체결금액3 — 체결된 금액 | — | yes |
| `output[].nccs_qty` | string (10) | 미체결수량 | — | yes |
| `output[].prcs_stat_name` | string (60) | 처리상태명 — 완료, 거부, 전송 | — | yes |
| `output[].rjct_rson` | string (60) | 거부사유 — 정상 처리되지 못하고 거부된 주문의 사유 | — | yes |
| `output[].rjct_rson_name` | string (60) | 거부사유명 | — | yes |
| `output[].ord_tmd` | string (6) | 주문시각 — 주문 접수 시간 | — | yes |
| `output[].tr_mket_name` | string (60) | 거래시장명 | — | yes |
| `output[].tr_natn` | string (3) | 거래국가 | — | yes |
| `output[].tr_natn_name` | string (3) | 거래국가명 | — | yes |
| `output[].ovrs_excg_cd` | string (4) | 해외거래소코드 — `NASD` 나스닥 / `NYSE` 뉴욕 / `AMEX` 아멕스 / `SEHK` 홍콩 / `SHAA` 중국상해 / `SZAA` 중국심천 / `TKSE` 일본 / `HASE` 베트남 하노이 / `VNSE` 베트남 호치민 | — | yes |
| `output[].tr_crcy_cd` | string (60) | 거래통화코드 | — | yes |
| `output[].dmst_ord_dt` | string (8) | 국내주문일자 | — | yes |
| `output[].thco_ord_tmd` | string (6) | 당사주문시각 | — | yes |
| `output[].loan_type_cd` | string (2) | 대출유형코드 — `00` 해당사항없음 등 sheet 본문 값 | — | yes |
| `output[].loan_dt` | string (8) | 대출일자 | — | yes |
| `output[].mdia_dvsn_name` | string (60) | 매체구분명 — 예: OpenAPI, 모바일 | — | yes |
| `output[].usa_amk_exts_rqst_yn` | string (1) | 미국애프터마켓연장신청여부 — Y/N | — | yes |
| `output[].splt_buy_attr_name` | string (60) | 분할매수/매도속성명 — 정규장 종료 주문 시에는 정규장 종료, 시간 입력 시에는 from~to 시간 표시 | — | yes |

본 sub-field 표는 주문번호(`odno`), 종목(`pdno`), 매수/매도(`sll_buy_dvsn_cd`), 주문수량(`ft_ord_qty`), 체결수량(`ft_ccld_qty`), 미체결수량(`nccs_qty`), 주문가격(`ft_ord_unpr3`), 체결가격(`ft_ccld_unpr3`), 처리상태명(`prcs_stat_name`), 주문시각(`ord_tmd`) 매핑에 필요한 field name 을 제공한다. 단, 모의 request 제약상 `CCLD_NCCS_DVSN="00"` 전체 조회만 가능하고 `ODNO` 단건 검색은 불가하므로, paper 구현은 전체 조회 후 client-side filtering 이 필요하다.

### 4.7.2 미체결내역 (`TTTS3018R`) Response `output[]` sub-fields (실전 only — 모의 미지원)

본 표는 `uploads/6.xlsx` 의 **`해외주식 미체결내역`** sheet 에서 추출한 미체결내역 응답 sub-field 정의이다. **§4.8 에 명시된 대로 모의투자에서 사용 불가하며, 본 저장소의 `KisBroker.get_open_orders()` 는 paper 환경에서 이 endpoint 를 호출하지 않는다**. 실전 라이브 확장의 완전성을 위해 catalog 화만 한다.

| Field | Type | 의미 | Confirmed |
| --- | --- | --- | --- |
| `output[].ord_dt` | string (8) | 주문일자 — 주문접수 일자 | yes |
| `output[].ord_gno_brno` | string (5) | 주문채번지점번호 — 계좌 개설 시 관리점으로 선택한 영업점의 고유번호 | yes |
| `output[].odno` | string (10) | 주문번호 — 접수한 주문의 일련번호 | yes |
| `output[].orgn_odno` | string (10) | 원주문번호 — 정정 또는 취소 대상 주문의 일련번호 | yes |
| `output[].pdno` | string (12) | 상품번호 — 종목코드 | yes |
| `output[].prdt_name` | string (60) | 상품명 — 종목명 | yes |
| `output[].sll_buy_dvsn_cd` | string (2) | 매도매수구분코드 — `01`=매도, `02`=매수 | yes |
| `output[].sll_buy_dvsn_cd_name` | string (60) | 매도매수구분코드명 — 매수매도구분명 | yes |
| `output[].rvse_cncl_dvsn_cd` | string (2) | 정정취소구분코드 — `01`=정정, `02`=취소 | yes |
| `output[].rvse_cncl_dvsn_cd_name` | string (60) | 정정취소구분코드명 — 정정취소구분명 | yes |
| `output[].rjct_rson` | string (60) | 거부사유 — 정상 처리되지 못하고 거부된 주문의 사유 | yes |
| `output[].rjct_rson_name` | string (60) | 거부사유명 — 정상 처리되지 못하고 거부된 주문의 사유명 | yes |
| `output[].ord_tmd` | string (6) | 주문시각 — 주문 접수 시간 | yes |
| `output[].tr_mket_name` | string (60) | 거래시장명 | yes |
| `output[].tr_crcy_cd` | string (3) | 거래통화코드 — `USD` 미국달러 / `HKD` 홍콩달러 / `CNY` 중국위안화 / `JPY` 일본엔화 / `VND` 베트남동 | yes |
| `output[].natn_cd` | string (3) | 국가코드 | yes |
| `output[].natn_kor_name` | string (60) | 국가한글명 | yes |
| `output[].ft_ord_qty` | string (10) | FT주문수량 — 주문수량 | yes |
| `output[].ft_ccld_qty` | string (10) | FT체결수량 — 체결된 수량 | yes |
| `output[].nccs_qty` | string (10) | 미체결수량 | yes |
| `output[].ft_ord_unpr3` | string (26) | FT주문단가3 — 주문가격 | yes |
| `output[].ft_ccld_unpr3` | string (26) | FT체결단가3 — 체결된 가격 | yes |
| `output[].ft_ccld_amt3` | string (23) | FT체결금액3 — 체결된 금액 | yes |
| `output[].ovrs_excg_cd` | string (4) | 해외거래소코드 — `NASD` 나스닥 / `NYSE` 뉴욕 / `AMEX` 아멕스 / `SEHK` 홍콩 / `SHAA` 중국상해 / `SZAA` 중국심천 / `TKSE` 일본 / `HASE` 베트남 하노이 / `VNSE` 베트남 호치민 | yes |
| `output[].prcs_stat_name` | string (60) | 처리상태명 | yes |
| `output[].loan_type_cd` | string (2) | 대출유형코드 — `00` 해당사항없음 등 sheet 본문 값 | yes |
| `output[].loan_dt` | string (8) | 대출일자 — 대출 실행일자 | yes |
| `output[].usa_amk_exts_rqst_yn` | string (1) | 미국애프터마켓연장신청여부 — Y/N | yes |
| `output[].splt_buy_attr_name` | string (60) | 분할매수속성명 — 정규장 종료 주문 시에는 정규장 종료, 시간 입력 시에는 from~to 시간 표시 | yes |

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

## 다음 작업 가이드

1. 사용자가 KIS Open API 공식 개발자 포털 또는 신뢰 가능한 KIS 공식 문서에서 위 `<TBD>` 항목을 직접 확인합니다.
2. 항목별로 `Confirmed` 값을 `yes`로 변경하고 값을 채워 넣습니다.
3. `Confirmed` 값이 `yes`인 항목만 별도 mvp에서 `app/broker/kis.py`에 HTTP로 연결합니다.
4. 본 저장소는 사용자가 확인하지 않은 값은 절대 사용하지 않습니다.

## 보안

- 실제 app key, app secret, 계좌번호, access token, refresh token은 이 문서에 절대 기록하지 않습니다. 모두 `.env`(gitignored)에만 둡니다.
- 본 문서가 커밋된 형태로 git에 들어가도 자격증명 누출이 없도록 합니다.

# KIS_2 — Codex 구현 요약

## 1. Files Changed

- `docs/kis/MISSING_OFFICIAL_VALUES.md` (§2 와 §4 본문 교체)
- `projects/paper-trading/docs/ai/jobs/KIS_2/patch.md` (본 파일)

Pre-existing unrelated dirty files were left untouched.

## 2. Implementation Summary

### 채워진 값 — §2 해외주식 계좌

Paper-지원 endpoint 3 종:

- 해외주식 잔고 `VTTS3012R` (`/inquire-balance`)
- 해외주식 매수가능금액 `VTTS3007R` (`/inquire-psamount`)
- 해외주식 체결기준 현재잔고 `VTRP6504R` (`/inquire-present-balance`, 모의는 `output3` 만 사용 가능)

Paper-미지원 endpoint 4 종 (실전 TR_ID 만 명시):

- 해외주식 결제기준 잔고 `CTRP6010R`
- 해외주식 일별거래내역 `CTOS4001R`
- 해외주식 기간손익 `TTTS3039R`
- 해외증거금 통화별조회 `TTTC2101R`

공통 헤더 / 거래소 (모의: NASD/NYSE/AMEX) / 통화 (USD/HKD/CNY/JPY/VND) 정리 완료. 잔고 응답의 `output1[]` (포지션) / `output2` (계좌 집계) 핵심 필드와 매수가능금액 응답의 `output` 핵심 필드를 catalog 화.

### 채워진 값 — §4 모의투자 주문

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

### 부족한 값 (`<TBD>` 로 남긴 항목)

- 모의에서 매매 가능한 정확한 종목 list (주문 sheet 개요만 "일부 종목" 명시, 종목 list 부재).
- 체결기준 현재잔고 `output3` 의 sub-field 상세 (모의에서 사용 가능한 유일한 응답이지만 sub-field 표는 별 job 으로 catalog 화 권장).
- 주문체결내역 `output[]` array sub-field 상세.
- 아시아 거래소 (`SEHK`/`SHAA`/`SZAA`/`TKSE`/`HASE`/`VNSE`) 의 모의 TR_ID full list (6.xlsx 주문 sheet `tr_id` 셀 본문에 일부 명시되어 있으나 본 catalog 는 미국 + 대표 아시아만 표시. 필요시 별 job 으로 보강).

## 3. Safety Confirmation

- 코드 / 테스트 변경 0건.
- `MISSING_MARKET_DATA_VALUES.md` 무변동.
- §1 OAuth / §3 시세 / 정책 / 다음 작업 가이드 / 보안 섹션 무변동.
- `OrderType.MARKET` 가드 / live trading 가드 / RiskEngine / OMS / PaperBroker / KIS adapter 정책 변동 0건.
- 자동 git commit / push / merge / deploy 수행 안 함.

안전 grep clean:

```text
grep -n "Bearer eyJ\|appkey=\|appsecret=\|access_token=" docs/kis/MISSING_OFFICIAL_VALUES.md
Result: 0 lines

grep -n "12345678\|fake-key\|fake-secret" docs/kis/MISSING_OFFICIAL_VALUES.md
Result: 0 lines

grep -nE "import (requests|httpx|aiohttp|urllib3)" docs/kis/MISSING_OFFICIAL_VALUES.md
Result: 0 lines
```

Pre-existing unrelated dirty file still present and not modified by this job:

- `projects/paper-trading/app/api/server.py`

## 4. Test Results

From `/root/ai-dev-center/projects/ai-team/projects/paper-trading`:

```text
.venv/bin/python -m compileall app tests
Result: passed
```

`pytest` was not run because KIS_2 is document-only and `compileall` is the required check.

## 5. Remaining TODOs

- **`api-account-001` (해외주식 계좌 / 잔고 / 매수가능금액 / 체결기준 현재잔고 paper HTTP 연결)**: 진행 가능. 잔고 (`VTTS3012R`) 와 매수가능금액 (`VTTS3007R`) 의 endpoint / TR ID / headers / request fields / response fields 가 모두 `Confirmed: yes`. 체결기준 현재잔고 (`VTRP6504R`) 는 모의 `output3` 한정이라 부분 구현 가능. 후속 job 은 §2 의 catalog 만 참고하고 추측 금지.
- **`api-orders-paper-001` (해외주식 모의 주문 / 정정·취소 paper HTTP 연결)**: 진행 가능. 주문 (`VTTT1002U` 미국매수 / `VTTT1001U` 미국매도) 과 정정취소 (`VTTT1004U`) 의 endpoint / TR ID / headers / request body fields / response body fields 가 모두 `Confirmed: yes`. **단 LIMIT 만 허용** — 본 저장소의 `OrderType.MARKET` 3중 가드를 그대로 유지하고 `ORD_DVSN=00` 만 송신한다. `KIS_ORDER_DRY_RUN=true` 기본값 + `validate_kis_order_request` pre-flight + OMS 단독 executable order 생성 + Strategy/Agent 의 broker 직접 호출 금지 정책 그대로.
- 미체결 (`TTTS3018R`) / 예약주문조회 / 미국주간 / 지정가주문번호·체결내역 endpoint 는 모의 미지원이므로 paper 단계에서는 `NotImplementedError` 유지.

READY FOR REVIEW

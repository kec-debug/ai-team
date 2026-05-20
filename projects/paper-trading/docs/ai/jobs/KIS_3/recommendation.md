# KIS_3 — Recommendation

## 1. catalog 갱신 요약

- §4.7.1: 주문체결내역 (`VTTS3035R`) Response `output[]` sub-fields 를 `uploads/6.xlsx` 의 `해외주식 주문체결내역` sheet 에서 추출해 `Confirmed: yes` 로 채웠다. 총 32개 sub-field.
- §4.7.2: 미체결내역 (`TTTS3018R`) Response `output[]` sub-fields 를 `uploads/6.xlsx` 의 `해외주식 미체결내역` sheet 에서 추출해 catalog 화했다. 총 29개 sub-field. 단, `TTTS3018R` 은 §4.8 그대로 모의투자 미지원이다.
- §4.2: 별도 "주문상태 조회" endpoint 는 `API 목록` sheet rows 1-19 에서 발견되지 않았다. `주문상태` 검색은 별도 주문상태 endpoint 가 아니라 `해외주식 예약주문조회` sheet 의 예약주문 상태 필드(`ovrs_rsvn_ord_stat_cd`)만 반환했다. §4.2 는 변경하지 않았다.

## 2. audit decision matrix 갱신

| 기능 | KIS_2-check 결과 | KIS_3 후 결과 | 사유 |
| --- | --- | --- | --- |
| `get_open_orders` | BLOCKED-BY-DOCS | PARTIALLY READY | Native 미체결 endpoint `/inquire-nccs` (`TTTS3018R`) 는 여전히 모의 미지원. 다만 paper-supported `/inquire-ccnl` (`VTTS3035R`) 의 `output[]` 에 `odno`, `pdno`, `sll_buy_dvsn_cd`, `ft_ord_qty`, `ft_ccld_qty`, `nccs_qty`, `ft_ord_unpr3`, `prcs_stat_name`, `ord_tmd`, `ovrs_excg_cd` 가 confirmed 되어 전체 조회 후 `nccs_qty > 0` 등 client-side filtering 이 가능해졌다. |
| `get_fills` | PARTIALLY READY → 사실상 BLOCKED | PARTIALLY READY | Request 측은 이미 confirmed. §4.7.1 로 `odno`, `pdno`, `sll_buy_dvsn_cd`, `ft_ccld_qty`, `ft_ccld_unpr3`, `ft_ccld_amt3`, `tr_crcy_cd`, `ord_tmd`, `prcs_stat_name` 이 confirmed 되었다. 단, 별도 체결번호와 명확한 체결시각 필드는 확인되지 않아 구현은 주문번호 기반 fill projection 또는 sanitized broker rows 로 제한해야 한다. |
| `get_order_status` | BLOCKED-BY-DOCS | PARTIALLY READY | 별도 주문상태 endpoint 와 paper ODNO 검색은 여전히 없다. 하지만 `VTTS3035R` 전체 조회 결과에 `odno`, `orgn_odno`, `ft_ord_qty`, `ft_ccld_qty`, `nccs_qty`, `prcs_stat_name`, `rjct_rson`, `rjct_rson_name` 이 confirmed 되어, 날짜 범위 전체 조회 + client-side ODNO lookup 으로 부분 상태 매핑은 가능하다. |

## 3. 다음 작업

옵션 A: `api-orders-paper-003-query` (adapter-level query 3 기능).

`next-job-request.md` 초안을 작성했다.

선택 사유:

- 세 기능 모두 native/단건 endpoint 면에서는 제한이 남지만, §4.7.1 로 paper-supported `VTTS3035R` 응답 sub-field 이름이 확인되어 adapter-level partial implementation 이 가능하다.
- 다음 job 은 GET 전용 `KisQueryTransport` 를 새로 두고 `KisAccountTransport` 패턴을 재사용해야 한다. 기존 `KisOrderTransport` 는 POST 주문 전송 전용이므로 재사용하지 않는다.
- OMS 확장, GUI/status surface 변경, capabilities 공개는 별도 job 으로 둔다.

## 4. 차단점

- `get_open_orders`: `/inquire-nccs` 는 모의 미지원이므로 paper native open-order endpoint 는 없음. `/inquire-ccnl` 전체 조회 후 client-side filtering 만 가능.
- `get_fills`: 별도 fill id 와 명확한 체결시각 field 는 6.xlsx `해외주식 주문체결내역` sheet 에서 확인되지 않았다. 주문번호(`odno`) + 체결수량/단가/금액 기반 projection 으로 제한해야 한다.
- `get_order_status`: 별도 주문상태 endpoint 및 ODNO query 는 없음. 전체 조회 기간/페이지 범위 밖의 주문은 fail-closed 해야 한다.
- 모든 구현은 §4.7 request 제약을 유지해야 한다: `PDNO=""`, `SLL_BUY_DVSN="00"`, `CCLD_NCCS_DVSN="00"`, `SORT_SQN` default `DS`, `ORD_DT=""`, `ORD_GNO_BRNO=""`, `ODNO=""`.

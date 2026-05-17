# KIS Open API - Missing Market Data Values

본 문서는 KIS Open API 미국주식/해외주식 시세 조회 HTTP 연결을 구현하기 위한 공식 문서값 catalog입니다. 본 저장소는 KIS endpoint, TR ID, header, payload를 추측하지 않으며, 본 catalog의 `Confirmed: yes` 항목은 KIS Developers 공식 자료(2026-05-15 사용자 업로드 1.xlsx + 3.xlsx)에서 직접 확인된 값에 한정합니다.

본 문서는 `docs/kis/MISSING_OFFICIAL_VALUES.md`의 "해외주식/미국주식 시세" 항목을 보강하는 시세 전용 catalog입니다.

## 정책 (Option B — 2026-05-15 갱신)

- **시세(read-only) endpoint는 실전 도메인 사용을 허용**합니다. KIS가 모의투자에서 시세를 제한적으로만 제공하기 때문입니다(해외주식 현재체결가만 모의 지원, 현재가상세/현재가 호가는 모의 미지원).
- **주문/계좌/체결 endpoint는 본 변경에 영향 없이 모의투자 전용을 유지합니다.** `KisBroker`는 모의 도메인 + `KIS_ORDER_DRY_RUN=true` + 5+1단 차단을 그대로 유지합니다.
- 실전 시세용 `appkey`/`appsecret`은 `.env`에만 보관하며, 실제 키/시크릿/계좌번호/access token은 본 문서/저장소 어디에도 기록하지 않습니다.
- 본 catalog의 `Confirmed: yes`는 공식 자료에 명시된 값에 한해 부여합니다.
- `Confirmed: no` 또는 `partial`인 행은 공식 자료에 명시되지 않았거나 추가 확인이 필요한 항목이며, 해당 동작은 후속 mvp까지 fail-closed(`NotImplementedError`) 또는 보수적 fallback을 유지합니다.

## 1. 해외주식 시세 endpoint catalog

KIS는 해외주식 시세 정보를 3개 endpoint에 분산합니다: 체결가(가볍고 모의 지원) / 현재가상세(메타데이터 풍부) / 현재가 호가(bid/ask 10단).

### 1.1 공통 base URL

| 환경 | Base URL | 본 저장소 용도 | Confirmed |
| --- | --- | --- | --- |
| 실전 | `https://openapi.koreainvestment.com:9443` | 시세 read-only (Option B 허용) | yes |
| 모의 | `https://openapivts.koreainvestment.com:29443` | 해외주식 현재체결가, 주문/계좌 계열 | yes |

### 1.2 endpoint별 path / TR_ID

| 메뉴 | path | HTTP method | 실전 TR_ID | 모의 TR_ID | Confirmed |
| --- | --- | --- | --- | --- | --- |
| 해외주식 현재체결가 | `/uapi/overseas-price/v1/quotations/price` | GET | `HHDFS00000300` | `HHDFS00000300` | yes |
| 해외주식 현재가상세 | `/uapi/overseas-price/v1/quotations/price-detail` | GET | `HHDFS76200200` | 모의 미지원 | yes |
| 해외주식 현재가 호가 | `/uapi/overseas-price/v1/quotations/inquire-asking-price` | GET | `HHDFS76200100` | 모의 미지원 | yes |

### 1.3 공통 Request Header

| Header | 필수 | 값/형식 | Confirmed |
| --- | --- | --- | --- |
| `content-type` | 응답 측 필수, 요청 측 옵션 | `application/json; charset=utf-8` | yes |
| `authorization` | Y | `Bearer ${access_token}` (OAuth `/oauth2/tokenP` 발급) | yes |
| `appkey` | Y | 한국투자증권에서 발급, length 36 | yes |
| `appsecret` | Y | 한국투자증권에서 발급, length 180 | yes |
| `tr_id` | Y | 위 1.2의 endpoint별 TR_ID | yes |
| `custtype` | 현재체결가는 옵션, 현재가호가는 필수 | `B`(법인) / `P`(개인) | yes |
| `personalseckey`, `tr_cont`, `seq_no`, `mac_address`, `phone_number`, `ip_addr`, `gt_uid` | 대부분 옵션 (일부 법인 필수) | 본 저장소는 개인 사용자 가정으로 미설정 | yes |

### 1.4 Query Parameter (3개 endpoint 공통 골격)

| Param | 필수 | 설명 | 허용값 | Confirmed |
| --- | --- | --- | --- | --- |
| `AUTH` | Y | 사용자권한정보 | 공백 또는 Null | yes |
| `EXCD` | Y | 거래소코드 | `HKS`/`NYS`/`NAS`/`AMS`/`TSE`/`SHS`/`SZS`/`SHI`/`SZI`/`HSX`/`HNX`/`BAY`/`BAQ`/`BAA` | yes |
| `SYMB` | Y | 종목코드 | 예: `TSLA` (length ≤ 16) | yes |

## 2. Quote 응답 필드 매핑

### 2.1 단일 endpoint(현재체결가) 사용 — 모의/실전 둘 다, 단 bid/ask·timestamp 미제공

| Quote field | 현재체결가 응답 (`output.*`) | 비고 | Confirmed |
| --- | --- | --- | --- |
| `symbol` | `rsym` 파싱(`D` + EXCD 3자리 + SYMB) 또는 요청 SYMB echo | 예: `DNASAAPL` → AAPL | yes |
| `last` | `last` | 당일 조회시점 현재가 | yes |
| `volume` | `tvol` | 당일 누적 거래량 | yes |
| `bid` | 없음 | 호가 endpoint 별도 호출 필요 | <TBD> |
| `ask` | 없음 | 호가 endpoint 별도 호출 필요 | <TBD> |
| `timestamp` | 응답 필드 없음 | 응답 수신 시각으로 대체(TZ-aware) | <TBD> |
| `zdiv` | `zdiv` | 소수점 자리수 (가격 파싱 보조) | yes |
| 부가 | `base`(전일종가), `pvol`(전일거래량), `sign`(대비기호: 1상한/2상승/3보합/4하한/5하락), `diff`, `rate`, `tamt`, `ordy` | | yes |

### 2.2 현재체결가 + 현재가 호가 조합 (실전 전용) — Quote 완전체

| Quote field | 출처 | 필드 | Confirmed |
| --- | --- | --- | --- |
| `symbol` | 현재체결가 또는 호가 | `rsym` 파싱 | yes |
| `last` | 현재체결가 또는 호가 `output1` | `last` | yes |
| `bid` | 호가 `output2` | `pbid1` (최우선 매수호가) | yes |
| `ask` | 호가 `output2` | `pask1` (최우선 매도호가) | yes |
| `volume` | 현재체결가 또는 호가 | `tvol`(체결가) 또는 `bvol`+`avol`(호가 총잔량) | yes |
| `timestamp` | 호가 `output1` | `dymd`(YYYYMMDD) + `dhms`(HHMMSS) | partial (포맷 yes, 시간대 미명시) |
| 부가 호가 단계 | 호가 `output2` | 미국: `pbid1`~`pbid10`/`pask1`~`pask10` (10단). 그 외 거래소: 1단계만 | yes |

### 2.3 메타데이터 (현재가상세, 실전 전용)

| 항목 | 응답 필드 | Confirmed |
| --- | --- | --- |
| 호가단위 (tick size) | `e_hogau` | yes |
| 매매단위 | `vnit` | yes |
| 통화 | `curr` (예: `USD`) | yes |
| 상한가/하한가 | `uplp`/`dnlp` | yes |
| 52주 최고/최저 가격·일자 | `h52p`/`h52d`/`l52p`/`l52d` | yes |
| PER/PBR/EPS/BPS | `perx`/`pbrx`/`epsx`/`bpsx` | yes |
| 거래가능여부 | `e_ordyn` | yes |
| 업종(섹터) | `e_icod` | yes |
| ETP 분류명 | `etyp_nm` | yes |
| 시가/고가/저가 | `open`/`high`/`low` | yes |
| 시가총액 | `tomv` | yes |
| 상장주수 | `shar` | yes |
| 원환산 당일/전일 가격·환율 | `t_xprc`/`p_xprc`/`t_rate`/`p_rate` 등 | yes |

## 3. 호가단위 / 거래소 시간

| 항목 | 값 | Confirmed |
| --- | --- | --- |
| 거래소 코드 | `HKS`/`NYS`/`NAS`/`AMS`/`TSE`/`SHS`/`SZS`/`SHI`/`SZI`/`HSX`/`HNX`/`BAY`/`BAQ`/`BAA` | yes |
| 호가단위 (tick size) | 종목별 가변, 현재가상세 응답 `e_hogau` 사용 (실전 endpoint 필요) | yes |
| 거래소 timezone | KIS docs에 명시 부재. 본 저장소는 미국 EXCD(NAS/NYS/AMS/BAY/BAQ/BAA)를 EST/EDT로, 홍콩 HKS를 HKT 등 일반 시장 시간대로 가정 | no |
| 응답 timestamp 포맷 | 현재체결가는 timestamp 없음. 현재가 호가는 `dymd`(YYYYMMDD) + `dhms`(HHMMSS) 별도 필드 | yes |
| Stale quote 판단 기준 | KIS docs에 명시 부재. 본 저장소는 `max_age_seconds` 파라미터로 도메인 결정 | no |

## 4. 시세 종류 / 권한

| 항목 | 값 | Confirmed |
| --- | --- | --- |
| 시세 권한 | 무료시세(지연시세)만 API로 제공. 유료시세(실시간시세)는 API 미지원 | yes |
| 미국 지연시간 | 0분 지연 (나스닥 마켓센터에서 거래되는 호가 및 호가잔량 정보) | yes |
| 홍콩/일본/중국/베트남 지연 | 각 endpoint 개요에 분 단위 명시. 본 저장소는 미국 우선 | partial |
| Rate limit (초당/분당 호출) | endpoint별 명시 부재. KIS 공통 안내(별도 자료) 필요 | no |
| 동시 심볼 수 제한 | endpoint별 명시 부재. 별도 endpoint `해외주식 복수종목 시세조회`(`HHDFS76220000`, 실전 전용)가 다중 심볼 지원 | partial |

## 5. OAuth (시세 호출의 전제)

| 항목 | 값 | Confirmed |
| --- | --- | --- |
| Token 발급 endpoint | `POST /oauth2/tokenP` | yes |
| Token 발급 base URL | 실전 `https://openapi.koreainvestment.com:9443` / 모의 `https://openapivts.koreainvestment.com:29443` | yes |
| Request body fields (JSON) | `grant_type=client_credentials`, `appkey`, `appsecret` | yes |
| Response token field | `access_token` | yes |
| Response token type | `token_type=Bearer` (API 호출 시 `Authorization: Bearer ${access_token}`) | yes |
| Response expiry | `expires_in` (초, 약 86400), `access_token_token_expired` (`YYYY-MM-DD HH:MM:SS`) | yes |
| 재발급 정책 | 유효기간 24시간, 6시간 이내 재호출 시 기존 토큰 반환 | yes |

## 다음 작업 가이드

1. (KIS_1으로 완료) catalog 채우기.
2. (별 job 권장: `mvp-023b`) `KisMarketDataClient.get_quote()` 실제 HTTP 연결.
   - OAuth 토큰 캐시(6시간 유효 활용).
   - 현재체결가 호출(`symbol`/`last`/`volume`) + 응답 수신 시각을 `timestamp`로 사용.
   - 옵션: 같은 sweep에서 현재가 호가도 호출해 `bid`/`ask` 합쳐 Quote 완성.
3. `KisBroker` 주문 경로는 본 변경과 무관하게 모의 도메인 + `KIS_ORDER_DRY_RUN=true` 유지.
4. `.env`에 추가될 변수(`mvp-023b` 범위): `KIS_MARKET_DATA_APP_KEY`, `KIS_MARKET_DATA_APP_SECRET`, `KIS_MARKET_DATA_BASE_URL`(=실전 도메인). 기존 `KIS_APP_KEY`/`KIS_APP_SECRET`(모의)와 분리.
5. (별 job 권장: `KIS_2`) `MISSING_OFFICIAL_VALUES.md` §2 계좌 + §4 주문 catalog 채우기. 자료는 6.xlsx에 존재.

## 보안

- 실제 app key, app secret, 계좌번호, access token, refresh token은 본 문서/저장소 어디에도 기록하지 않습니다. 모두 `.env`(gitignored)에만 둡니다.
- 실전 시세용 키는 폭발 반경이 모의 키보다 큽니다: 사용자는 KIS 포털에서 IP 화이트리스트 설정을 권장합니다.
- 실전 키가 동시에 실전 주문 권한을 갖는 경우, 본 저장소의 `KIS_ORDER_DRY_RUN` / 5+1단 차단은 외부 침해로부터 키 자체를 보호하지 않습니다. KIS 포털에서 키 권한을 시세로 제한할 수 있다면 그렇게 설정해야 합니다.

## 관련 문서

- `docs/kis/MISSING_OFFICIAL_VALUES.md` §1 OAuth와 §3 시세는 본 문서로 보강 완료. §2 계좌와 §4 주문은 별 job(`KIS_2`)에서 자료 6.xlsx로 채울 예정.
- `docs/ai/jobs/KIS_1/` — 본 작업의 plan, codex-task, patch, review.
- `docs/ai/MASTER_TRADING_ROADMAP.md` — 전체 로드맵.

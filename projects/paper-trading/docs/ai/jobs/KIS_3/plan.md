# KIS_3 — KIS 미체결 / 체결 / 주문상태 조회 공식 응답 필드 catalog 보강

본 작업은 **docs-only catalog 보강**이다. 코드 변경 없음. KIS_2-check audit 가 `get_open_orders` / `get_fills` / `get_order_status` 의 단일 차단점으로 식별한 catalog gap C1 (`docs/kis/MISSING_OFFICIAL_VALUES.md` §4.7 의 `output[]` sub-field full list 가 `<TBD>`) 를 해소한다.

## 1. 요청 요약

KIS_2 가 `uploads/6.xlsx` (KIS Developers 공식 자료, 2026-05-19 사용자 업로드) 를 사용해 §2 (계좌) / §4 (주문) catalog 를 채웠지만, **§4.7 주문체결내역 (`VTTS3035R`) 의 response `output[]` array sub-field 표는 별 job 으로 미루었다** (§4.7 마지막 문단). 이로 인해 KIS_2-check 가 query 3 기능을 BLOCKED-BY-DOCS 로 분류했다.

KIS_3 는 같은 `uploads/6.xlsx` 의 **주문체결내역 sheet** 에서 `output[]` sub-field 표를 추출해 catalog 의 §4.7 (또는 신규 §4.11) 에 `Confirmed: yes` 행으로 추가한다. 보조적으로 **미체결내역 sheet** (paper 미지원이지만 실전 자료는 sheet 에 존재) 와 **API 목록 sheet** 의 주문상태 조회 관련 행도 검토해 별도 endpoint 존재 여부를 catalog 에 기록한다.

코드 / 테스트 변경 없음. 결과물은 catalog 본문 갱신 + audit decision matrix 갱신 + (조건 충족 시) `api-orders-paper-003-query` 의 request.ko.md 초안.

## 2. 작업 범위

포함:

- `docs/kis/MISSING_OFFICIAL_VALUES.md` §4.7 의 `output[]` sub-field 표 추가 (또는 §4.11 로 분리).
- `uploads/6.xlsx` 의 **주문체결내역 sheet** 에서 catalog 화 대상 컬럼:
  - sub-field name (예: `ovrs_pdno`, `ord_qty`, `ccld_qty`, `nccs_qty`, `ord_unpr`, `ccld_unpr`, `ord_tmd`, `ccld_dt`, `prcs_stat_name` 등 — 실제 이름은 sheet 확인 결과로 결정)
  - 한국어 의미
  - Type / 길이
  - 모의 제약 (sheet 에 명시된 경우)
  - Confirmed (자료에 명시되면 `yes`, 아니면 `<TBD>` / `no`)
- 미체결내역 sheet (`TTTS3018R`) 응답 sub-field 표 추가 — paper-미지원이지만 향후 라이브 작업의 완전성을 위해 기록 (`Confirmed: yes` 단 "모의 미지원" 명시).
- 별도 "주문상태 조회" endpoint 가 6.xlsx API 목록 sheet 에 존재하는지 재확인하고 결과를 §4.2 또는 §4.12 에 기록.
- KIS_2-check 의 audit decision matrix 갱신 — `get_open_orders` / `get_fills` / `get_order_status` 각각 READY / PARTIALLY READY / BLOCKED-BY-DOCS 재분류.
- 다음 작업 (`api-orders-paper-003-query`) 의 request.ko.md 초안 — **세 기능 중 최소 한 개라도 READY / PARTIALLY READY 가 되는 경우만** 작성.

제외 (절대 안 함):

- 코드 / 테스트 변경. `app/`, `tests/`, `pyproject.toml`, `README.md` 등 전부 무변동.
- `<TBD>` 또는 `Confirmed: no` 인 항목을 추측으로 채우기. **반드시 6.xlsx 의 실제 셀 본문에 명시된 값만 사용**.
- 6.xlsx 외 KIS 공식 자료 (개발자 포털 HTML 등) 를 새로 인용하는 것 — 본 job 의 source-of-truth 는 KIS_2 가 사용한 동일 파일.
- 실 secret / 계좌번호 / token / Bearer 원문 기록. 6.xlsx 에 그런 값이 들어 있을 가능성은 낮지만, sub-field 추출 과정에서 우연히 노출하지 않도록 주의.
- 외부 HTTP 라이브러리 도입. `openpyxl` / `pandas` 등 추가 의존성 도입 금지 — stdlib `zipfile` + `xml.etree.ElementTree` 만으로 `.xlsx` 읽기 가능.
- 자동 git commit / push / merge / deploy.
- GUI 파일 수정.
- `.env` / `.env.example` 변경.

## 3. 수정해야 할 파일

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `docs/kis/MISSING_OFFICIAL_VALUES.md` | MODIFY | §4.7 의 `output[]` sub-field 표 + 미체결내역 sub-field 표 (paper 미지원 명시) + 주문상태 조회 endpoint 존재 여부 결론 추가. 기존 `Confirmed: yes` 행과 §4.10 안전 정책은 무변동. |
| `projects/paper-trading/docs/ai/jobs/KIS_3/plan.md` | NEW | 본 문서. |
| `projects/paper-trading/docs/ai/jobs/KIS_3/codex-task.md` | NEW | Codex 가 6.xlsx 에서 sub-field 표를 추출해 catalog 를 갱신하는 단계별 지시. |
| `projects/paper-trading/docs/ai/jobs/KIS_3/recommendation.md` | NEW | catalog 갱신 후 `get_open_orders` / `get_fills` / `get_order_status` 분류 + 다음 작업 추천. Codex 가 작성. |
| `projects/paper-trading/docs/ai/jobs/KIS_3/next-job-request.md` | NEW (조건부) | `api-orders-paper-003-query` 의 request.ko.md 초안. **세 기능 중 최소 한 개가 READY/PARTIALLY READY 일 때만**. BLOCKED 만 남으면 생략하고 recommendation.md 에 "여전히 BLOCKED" 로 보고. |
| `projects/paper-trading/docs/ai/jobs/KIS_3/patch.md` | NEW | Codex 가 작성. |

손대지 않는 파일:

- `app/` 전체, `tests/` 전체, `pyproject.toml`, `README.md`, `.env`, `.env.example`.
- `docs/kis/` 안의 다른 파일 (있다면).
- 다른 job 디렉터리.

## 4. Codex 구현 지시문 (요지; 자세한 단계는 codex-task.md)

### 4.1 6.xlsx 안전 읽기

- `uploads/6.xlsx` 를 stdlib `zipfile.ZipFile` 로 열고, `xl/sharedStrings.xml` + `xl/worksheets/sheet*.xml` 을 읽어 셀 본문을 추출한다.
- 외부 의존성 (`openpyxl`, `pandas`) 도입 금지. 이미 KIS_2 가 동일 패턴으로 처리했을 가능성 — KIS_2 patch.md 참고.
- 추출 스크립트는 한 번만 실행하는 도구 성격이므로 `tests/` 또는 `app/` 에 commit 하지 않는다. 본 job 의 codex-task.md 에 inline shell + python one-liner 로 기록만 한다.

### 4.2 대상 sheet 식별

1. **주문체결내역 sheet** — KIS_2 가 §4.7 작성 시 참조한 sheet. sheet 이름은 6.xlsx 의 workbook.xml 의 `<sheet>` 엔트리에서 찾는다 (한국어 sheet 명 예상).
2. **미체결내역 sheet** — `TTTS3018R` (실전 only) 의 응답 정의. 모의 미지원이지만 catalog 완전성을 위해 함께 기록.
3. **API 목록 sheet** — "주문상태 조회" 별도 endpoint 존재 여부 재확인. KIS_2-check 가 "없음" 으로 잠정 결론. 본 job 은 6.xlsx 의 API list 행을 정렬하여 재확인.

### 4.3 추출 후 catalog 갱신 형식

§4.7 끝에 다음 형태의 표를 추가 (예시 — 실제 행은 sheet 확인 후 채움):

```markdown
### 4.7.1 주문체결내역 (`VTTS3035R`) Response `output[]` sub-fields

본 표는 `uploads/6.xlsx` 주문체결내역 sheet 의 응답 sub-field 표에서 직접 추출한 값이다. `Confirmed: yes` 행은 6.xlsx 에 명시된 값에 한정한다. 모의 제약은 sheet 에 명시된 경우만 표기한다.

| Field | Type | 의미 | 모의 제약 | Confirmed |
| --- | --- | --- | --- | --- |
| `output[].<actual_field_name>` | string | <의미> | <제약 또는 —> | yes |
| ... | ... | ... | ... | ... |
```

### 4.4 미체결내역 (실전) 처리

§4.8 "모의투자 미지원 endpoint 목록" 아래 또는 §4.7.2 신규 절로:

```markdown
### 4.7.2 미체결내역 (`TTTS3018R`) Response `output[]` sub-fields (실전 only — 본 저장소 미사용)

본 sheet 는 6.xlsx 의 미체결내역 sheet 에서 추출한다. **모의투자 미지원이므로 본 저장소의 `KisBroker.get_open_orders()` 는 paper 환경에서 호출할 수 없다**. 실전 라이브 확장 시 참조를 위해 catalog 화만 한다.

(테이블)
```

### 4.5 audit decision matrix 갱신

`recommendation.md` 에서 KIS_2-check 의 audit 결정을 재평가:

- **`get_open_orders`**:
  - paper-native endpoint (`inquire-nccs`) 가 모의 미지원이라는 사실은 6.xlsx 가 동일하게 명시.
  - 우회 경로 (`inquire-ccnl` 의 `CCLD_NCCS_DVSN="02"`) 도 paper 에서 사용 불가 (§4.7 의 모의 제약).
  - C1 해소 후에도 **paper 에서 status 필드로 client-side 필터링** 이 가능한지를 새 sub-field 표에서 확인. 가능하면 PARTIALLY READY, 불가능하면 여전히 BLOCKED.
- **`get_fills`**:
  - request 측은 §4.7 에서 이미 `Confirmed: yes`. 신규 §4.7.1 의 sub-field 표가 fill id / symbol / side / 체결수량 / 체결가 / 체결시각 / (가능하면) commission 을 포함하면 **READY**. 일부 누락 시 PARTIALLY READY.
- **`get_order_status`**:
  - paper 에서 ODNO 검색 불가 (§4.7 의 `ORD_DT`/`ORD_GNO_BRNO`/`ODNO` 모두 `""` 필수 제약) 는 변동 없음.
  - 신규 sub-field 표에 status / 잔여수량 컬럼이 있으면, 전체 fetch + client-side 단건 lookup 으로 PARTIALLY READY 구현 가능.

### 4.6 next-job-request.md 초안 작성 조건

세 기능 중 **최소 한 개가 READY 또는 PARTIALLY READY** 면 `next-job-request.md` 에 `api-orders-paper-003-query` 의 request.ko.md 초안을 작성. 초안은:

- 구현 범위를 READY / PARTIALLY READY 기능으로만 한정.
- 여전히 BLOCKED 인 기능은 명시적으로 NotImplementedError 유지.
- catalog §4.7.1 / §4.7.2 의 `Confirmed: yes` 필드만 사용.
- paper 제약 (PDNO="", CCLD_NCCS_DVSN="00", SORT_SQN default, ODNO="") 그대로 준수.
- 새 transport 클래스 추가 필요성 평가 (현재 `KisOrderTransport` 는 POST 전용; query 는 GET — `KisAccountClient` 의 `UrllibAccountTransport` 패턴 재사용 권고).

세 기능 모두 BLOCKED 면 `next-job-request.md` 생략하고 `recommendation.md` 에 "추가 KIS 측 정책 변경 또는 catalog 확장이 필요" 라고 명시.

### 4.7 안전 grep

- `grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3|openpyxl|pandas)" docs/ai/jobs/KIS_3` → 0 lines.
- `grep -rn "Bearer eyJ\|access_token=eyJ\|appkey=eyJ" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md` → 0 lines (forbidden literal grep, 단 본 plan / codex-task / patch 의 instruction 텍스트 인용은 예외).
- `grep -rn "12345678\|fake-account\|fake-key" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md` → 0 lines.

## 5. 검증 기준

- catalog §4.7.1 (주문체결내역 sub-fields) 가 추가됐고 모든 행이 6.xlsx 셀 본문에서 인용 가능.
- 추측으로 채운 행 없음 — 6.xlsx 에서 확인되지 않는 값은 `<TBD>` 유지.
- recommendation.md 가 세 기능을 READY / PARTIALLY READY / BLOCKED-BY-DOCS 중 하나로 명확히 분류.
- 분류가 PARTIALLY READY 인 경우, 부분 구현 가능 범위와 fail-closed 유지 범위가 분리되어 있음.
- 최소 한 개 READY/PARTIALLY READY 시 `next-job-request.md` 가 catalog 의 `Confirmed: yes` 행만 사용하도록 작성됨.
- 코드 / 테스트 / `.env` / GUI / `app/` / `tests/` 변경 없음.
- 안전 grep clean.
- `patch.md` 에 다음 포함:
  - 수정 파일 목록
  - 6.xlsx 의 어떤 sheet 에서 어떤 sub-field 를 추출했는지
  - 각 행의 출처 셀 좌표 또는 sheet 이름 (재현성)
  - audit decision matrix 결과
  - 안전 grep 결과
  - Claude 검증 요청 프롬프트
  - Follow-up Codex Prompt 작성 규칙

## 6. 리뷰 체크리스트

- [ ] §4.7.1 의 모든 `Confirmed: yes` 행이 6.xlsx 의 실제 셀에서 인용 가능.
- [ ] §4.7.2 가 미체결내역을 catalog 화하되 "모의 미지원" 을 명시.
- [ ] 추측 / fabrication 0 건. 확인 안 된 항목은 `<TBD>` 유지.
- [ ] §4.7 의 기존 `Confirmed: yes` 행 (request query 측) 무변동.
- [ ] §4.10 안전 정책 무변동.
- [ ] `<TBD>` → `Confirmed: yes` 변경된 항목은 추출 출처 (sheet/cell) 가 patch.md 에 기록됨.
- [ ] recommendation.md 의 분류가 catalog 의 실제 sub-field 와 일치.
- [ ] `next-job-request.md` (있다면) 가 BLOCKED 기능을 절대 포함하지 않음.
- [ ] 코드 / 테스트 / `.env` / GUI 무변동.
- [ ] 외부 의존성 (`openpyxl`, `pandas` 등) 추가 없음.
- [ ] 실 secret / 계좌번호 / token 노출 없음.
- [ ] 자동 git commit / push / merge / deploy 수행 없음.

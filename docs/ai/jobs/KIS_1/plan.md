## 1. 요청 요약

비개발자인 사용자가 KIS Developers 공식 자료를 `uploads/1.xlsx` ~ `uploads/6.xlsx`(2026-05-15 업로드)로 직접 제공함. KIS_1은 그 중 1.xlsx의 `[해외주식] 기본시세` 3개 시트(`해외주식 현재체결가`, `해외주식 현재가상세`, `해외주식 현재가 호가`)와 3.xlsx의 OAuth 시트(`접근토큰발급(P)`)에서 추출한 공식 값으로 `docs/kis/MISSING_MARKET_DATA_VALUES.md`를 채우는 docs-only 작업.

### 핵심 발견 (확인 완료)

- **모의투자에서 호출 가능한 시세 endpoint는 `해외주식 현재체결가` 단 하나**. 단, 응답에 bid/ask·timestamp가 없음.
- `해외주식 현재가상세`(`HHDFS76200200`)와 `해외주식 현재가 호가`(`HHDFS76200100`)는 **모의 미지원**, 실전 도메인에서만 호출 가능.
- 사용자가 옵션 B(시세 read-only는 실전 도메인 허용, 주문은 모의 전용 유지)를 선택. 본 작업이 그 정책 갱신을 catalog 문서에 반영.

### 정책 변경 요약 (Option B)

- `MISSING_MARKET_DATA_VALUES.md`의 "실전 endpoint는 저장소에 추가하지 않음" 문구를 **시세 read-only 한정으로 완화**. 주문/계좌/체결 endpoint에 대해서는 모의투자 전용 정책 그대로.
- 실제 HTTP 연결(`KisMarketDataClient.get_quote()`)은 본 KIS_1 범위 아님. 별 후속 job(`mvp-023b`)에서 처리.
- 실전 시세용 app key/secret은 사용자가 KIS 포털에서 별도 발급해 `.env`에만 두며, 본 저장소 어디에도 키/시크릿/계좌번호/토큰을 기록하지 않음.

### 안전 원칙 (변경 없음)

- live trading 비활성 유지. `OrderType.MARKET` 부재 유지. `KIS_ORDER_DRY_RUN=true` 기본값 유지.
- `KisBroker`(주문) 도메인은 모의 base URL 유지. 5+1단 차단(`Settings`/`load_settings`/`RiskEngine`/`OMS`/`POST /paper/run`/`KisBroker.__init__`) 변경 없음.
- 외부 HTTP 라이브러리 import 추가 금지(본 작업은 docs only).
- 실 KIS app key/secret/계좌번호/access token/refresh token을 catalog 또는 codex-task 어느 자리에도 기록하지 않음.
- KIS endpoint/TR ID/payload/header **추측 금지** — 본 작업은 사용자 업로드 공식 자료에서 추출한 값만 사용.
- `git commit` / `push` / `merge` / `deploy` 자동화 금지.

---

## 2. 작업 범위

### 포함 (In scope)

A. **`docs/kis/MISSING_MARKET_DATA_VALUES.md` 전면 갱신** (Codex 적용):
- 정책 섹션을 옵션 B로 교체.
- §1 endpoint catalog: 3개 시세 endpoint의 base URL/path/method/TR_ID/모의지원여부.
- §1 Request Header / Query Parameter 표.
- §2 Quote 응답 필드 매핑: (2.1) 현재체결가만 사용 시, (2.2) 현재체결가 + 호가 조합 시, (2.3) 현재가상세 메타데이터.
- §3 호가단위 / 거래소 시간.
- §4 시세 종류 / 권한.
- §5 OAuth 토큰 발급 (시세 호출의 전제).
- 각 행에 `Confirmed: yes`(공식 자료 명시) 또는 `Confirmed: no/partial`(자료에 명시 부재) 표기.
- `<TBD>` 행은 자료에 명시되지 않은 항목만 남김(rate limit / 거래소 timezone / staleness 판단 기준 등).

B. **`projects/paper-trading/tests/test_missing_market_data_values_doc.py` 갱신**:
- 현재 `test_doc_has_no_confirmed_yes_entries`가 "Confirmed: yes 부재"를 단정 → KIS_1로 인해 실제 confirmed 값이 들어가므로 이 단정은 **양방향 검증**으로 교체:
  - `Confirmed: yes`가 **존재**(공식 자료 반영) AND `Confirmed: no` 또는 `Confirmed: partial`도 **존재**(미확인 항목 보존).
- 다음 가드는 유지/강화:
  - 파일 존재.
  - 필수 섹션 마커(`현재가`, `Quote`, `응답 필드`, `호가단위`, `Confirmed`).
  - 실 키/시크릿 prefix 부재(`PSNFD`, `PKID`, `AKIA`, `sk-`, `ghp_`).
  - **추가 가드**: `appkey=`, `appsecret=`, `Bearer ey`(실 JWT 시작 패턴), 8자리 이상 연속 숫자 후 `-\d{2}`(계좌번호 패턴) 미존재.

C. **`docs/ai/jobs/KIS_1/patch.md`** (Codex 작성): 적용 요약, 변경 파일, 안전 grep 결과, 테스트 결과.

### 제외 (Out of scope; 절대 만지지 않음)

- `app/` 하 모든 코드 (특히 `app/broker/kis.py`, `app/broker/kis_quote_mapper.py`, `app/domain/quote.py`, `app/config.py`).
- 새 외부 HTTP 라이브러리 import.
- `.env`, `.env.example`, `.gitignore` 변경. **실전 시세 키 환경변수 추가는 후속 `mvp-023b`에서 처리.**
- `docs/kis/MISSING_OFFICIAL_VALUES.md`. (자료 6.xlsx로 §2 계좌/§4 주문 채우는 작업은 별 job `KIS_2` 권장.)
- 실주문, 시장가 주문, RiskEngine/OMS 우회, Strategy의 broker 직접 호출.
- 자동 `git commit` / `push` / `merge` / 배포.

---

## 3. 수정해야 할 파일

| 파일 | 동작 | 작성자 |
| --- | --- | --- |
| `docs/kis/MISSING_MARKET_DATA_VALUES.md` | 전면 교체 (codex-task §A 본문) | Codex |
| `projects/paper-trading/tests/test_missing_market_data_values_doc.py` | `Confirmed: yes 부재` 단정을 양방향 검증으로 교체 + 안전 가드 추가 | Codex |
| `docs/ai/jobs/KIS_1/patch.md` | 신규 — Codex 적용 요약 | Codex |
| `docs/ai/jobs/KIS_1/plan.md` | 본 문서 (수정 완료) | Claude |
| `docs/ai/jobs/KIS_1/codex-task.md` | 본 plan과 함께 갱신 | Claude |

**그 외 파일 절대 미변경.** 특히 `app/`, `projects/paper-trading/scripts/`, `imports/`, `web/`, `prompts/`, `docs/ai/MASTER_TRADING_ROADMAP.md` 변경 없음.

---

## 4. Codex 구현 지시문

Codex가 수행할 작업은 `docs/ai/jobs/KIS_1/codex-task.md`에 본문까지 완성된 형태로 제공함. 요약:

1. `docs/kis/MISSING_MARKET_DATA_VALUES.md`를 codex-task §A의 본문으로 **전면 교체**. 본문은 KIS Developers 공식 자료(2026-05-15 업로드 1.xlsx + 3.xlsx)에서 직접 추출한 값으로 채워져 있음. Codex는 그 본문에 단 한 줄도 추가/추측/보강하지 말 것.
2. `projects/paper-trading/tests/test_missing_market_data_values_doc.py`를 codex-task §B의 본문으로 교체.
3. 안전 grep:
   - 변경 후 `docs/kis/MISSING_MARKET_DATA_VALUES.md` 본문에 `PSNFD`/`PKID`/`AKIA`/`sk-`/`ghp_`/`appkey=`/`appsecret=`/`Bearer eyJ`/10자리 연속 숫자(계좌번호 패턴) 미존재 확인.
4. `python -m compileall app tests`와 `python -m pytest -p no:cacheprovider` 실행. 본 작업은 docs + 1개 테스트 파일 갱신만이므로 기존 214 PASS 유지 + `test_missing_market_data_values_doc.py`의 갱신된 단정 PASS.
5. `docs/ai/jobs/KIS_1/patch.md` 작성: 변경 파일 목록 + 안전 grep 결과 + 테스트 결과 + commit/push/merge 미실행 확인.
6. `git commit` / `push` / `merge` / 배포 **금지**.

---

## 5. 테스트 기준

### Codex 적용 후 PASS 조건

- `test_doc_exists` PASS.
- `test_doc_has_required_sections` PASS — 마커 `현재가`, `Quote`, `응답 필드`, `호가단위`, `Confirmed`, `<TBD>` 모두 존재(rate limit 등 `<TBD>` 항목이 남아 있어 마커가 보존됨).
- (갱신 후) `test_doc_has_confirmed_status_mix` PASS — `Confirmed: yes`와 `Confirmed: no`(또는 `partial`) 둘 다 존재.
- (갱신 후 가드) `test_doc_does_not_leak_real_secrets` PASS — 기존 prefix + 추가 패턴(`appkey=`, `appsecret=`, `Bearer eyJ`, 계좌번호 패턴) 미존재.
- 전체 suite `pytest -p no:cacheprovider`: 214 PASS 유지 (기존 회귀 0건).
- `python -m compileall app tests` 무오류.

### 안전 grep 단정 (Codex가 patch.md에 기록)

`docs/kis/MISSING_MARKET_DATA_VALUES.md`에 대해:

| 패턴 | 결과 |
| --- | --- |
| `PSNFD`, `PKID`, `AKIA`, `sk-`, `ghp_` | 0건 |
| `appkey=` (실 키 형태) | 0건 |
| `appsecret=` (실 키 형태) | 0건 |
| `Bearer eyJ` 또는 그 뒤에 실 JWT 패턴 | 0건 |
| 계좌번호 패턴 (예: `\d{8}-\d{2}` 또는 연속 10+자리 숫자) | 0건 |

---

## 6. 리뷰 체크리스트

### 콘텐츠

- [ ] `MISSING_MARKET_DATA_VALUES.md`의 모든 endpoint/TR_ID/path/header/query 값이 codex-task §A 본문과 byte-level 일치.
- [ ] Codex가 본 plan에 없는 endpoint/TR_ID를 추가하지 않음.
- [ ] `Confirmed: yes` 표시는 공식 자료 명시 항목에만 부여. 자료에 명시되지 않은 항목은 `Confirmed: no` 또는 `partial`로 유지.
- [ ] 정책 섹션이 "Option B: 시세 read-only는 실전 도메인 허용, 주문은 모의 전용 유지"로 명확히 갱신됨.
- [ ] 다음 작업 가이드에 `mvp-023b`(시세 HTTP 연결), `KIS_2`(주문/계좌 catalog), `.env`에 추가될 변수 이름이 명시됨.

### 안전

- [ ] `MISSING_MARKET_DATA_VALUES.md`와 `codex-task.md` 어디에도 실 app key/app secret/access token/계좌번호 0건.
- [ ] `app/`, `.env`, `.env.example`, `.gitignore`, prompts, scripts 변경 0건.
- [ ] 외부 HTTP 라이브러리 import 추가 0건.
- [ ] `KisMarketDataClient.get_quote()`는 그대로 `NotImplementedError` 유지(코드 본문 미접촉).
- [ ] `KisBroker`(주문) 변경 0건. 모의 도메인 + `KIS_ORDER_DRY_RUN=true` 유지.
- [ ] `OrderType.MARKET` 부재 유지.
- [ ] live trading 활성화 변경 0건.

### 테스트 / 프로세스

- [ ] `test_missing_market_data_values_doc.py`의 단정 변경이 plan §2.B와 byte-level 일치.
- [ ] 전체 suite 214 PASS 유지.
- [ ] `compileall` 무오류.
- [ ] `patch.md`에 변경 파일/안전 grep/테스트 결과/commit-skip 확인 기록.
- [ ] commit / push / merge / 배포 자동화 0건.

### 사람이 직접 해야 할 후속 액션

1. `git status`, `git diff`로 변경 범위 검증.
2. commit 시 다음만 staging:
   - `docs/kis/MISSING_MARKET_DATA_VALUES.md`
   - `projects/paper-trading/tests/test_missing_market_data_values_doc.py`
   - `docs/ai/jobs/KIS_1/`
3. **다음 단계**: 별 job 두 개로 분리해 진행 권장:
   - **`mvp-023b`** — `KisMarketDataClient.get_quote()` 실제 HTTP 연결. 옵션 B의 실전 시세 도메인 + OAuth + 현재체결가(+ 선택적 현재가 호가). `.env`에 `KIS_MARKET_DATA_APP_KEY`/`KIS_MARKET_DATA_APP_SECRET`/`KIS_MARKET_DATA_BASE_URL` 추가. 코드 변경 + 새 테스트.
   - **`KIS_2`** — 자료 6.xlsx 기반으로 `MISSING_OFFICIAL_VALUES.md` §2 계좌 + §4 주문 catalog 채우기. docs only.
4. **KIS 포털 액션** (사용자):
   - 실전 KIS app key/secret 발급(시세 권한이 별도 분리 가능하면 그렇게).
   - IP 화이트리스트 설정 권장.
   - 발급된 키를 `.env`에만 보관(저장소 어디에도 기록 금지). `.env.example`에 변수 이름만 추가하는 변경은 `mvp-023b` 범위.
5. 직전 채팅에서 노출된 KIS Developers 포털 로그인(`kec1003 / ZWxn7aD1`)은 **즉시 KIS 포털에서 비밀번호 변경**.

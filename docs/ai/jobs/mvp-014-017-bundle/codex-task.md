# Codex Task — mvp-014-017-bundle: KIS 공식 문서값 갭 정리 + 보류된 HTTP 작업 명문화

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-014-017-bundle/plan.md` and `docs/ai/jobs/mvp-014-017-bundle/request.ko.md` first.
>
> **중요**: 사용자가 명시한 안전 정책에 따라, KIS 공식 문서값이 저장소에 없으므로 **mvp-015/016/017의 HTTP 구현은 모두 보류**된다. Codex가 만들 수 있는 것은 mvp-014 산출물(공식 문서값 갭 분석 doc) + 작은 status 보강 + 테스트뿐이다. KIS endpoint URL, TR ID, payload는 **절대 추측 금지**.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-014-017-bundle`
- 대상: `docs/kis/MISSING_OFFICIAL_VALUES.md` (신규) + `projects/paper-trading/app/api/routes.py` + `projects/paper-trading/README.md` + 테스트 2개 + `patch.md`.

## 사전 점검 (Codex 첫 단계)

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: "126 tests collected" (or higher)

grep -q "kis_order_dry_run" app/config.py && echo "OK config.kis_order_dry_run"
grep -q "class KisHttpClient" app/broker/kis.py && echo "OK KisHttpClient"
grep -q "sanitize_kis_response" app/broker/kis.py && echo "OK sanitize_kis_response"
grep -q "KisOrderRejectedError" app/broker/kis.py && echo "OK KisOrderRejectedError"
grep -q "KIS_ORDER_DRY_RUN" .env.example && echo "OK .env.example dry_run"
test -d ../../docs/kis && echo "WARN: docs/kis already exists" || echo "OK docs/kis absent (will be created)"
```

위 5개 OK + docs/kis absent → 정상 진행. 누락 시 `patch.md` Remaining TODOs에 기록하고 작업 중단.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, KIS 실제 endpoint URL / TR ID / payload / app key / app secret / account number 변경/생성/읽기/노출 금지.
- **KIS endpoint URL, path, TR ID, header 값, payload 형식을 어떤 파일에도 추가하지 마.** `docs/kis/MISSING_OFFICIAL_VALUES.md` 포함. `<TBD>` placeholder + 필드 이름/설명만.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3` 등) 어떤 파일에도 import 금지.
- 실주문 코드, 실제 HTTP 호출 코드 신설 금지. 모든 KIS HTTP 메서드는 기존 `NotImplementedError`/`dry-run` 동작 그대로 유지.
- live trading 활성화 금지.
- `OrderType`에 MARKET 멤버 추가 금지.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis*` import하면 안 됨(grep 검증).
- OMS의 `_risk`/`_broker` private 유지. KIS는 활성 broker로 연결되지 않음.
- `/paper/status`나 어떤 응답에 raw key/secret/account/access_token 노출 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- **본 작업 범위 외 파일 변경 금지.** mvp-001..mvp-013 산출물, `app/broker/kis.py`, `app/config.py`, `app/risk/`, `app/oms/`, `app/runtime/`, `app/strategy/`, `app/domain/`, `app/broker/{base,paper,alpaca_paper}.py`, `app/api/server.py`, `app/main.py`, `.env.example`, 프로젝트/루트 `.gitignore`, `imports/`, `web/`, `prompts/`, `scripts/`, `examples/` 모두 미변경.
- `pip install` 실행 금지.
- 학습 데이터에 KIS Open API 정보가 있더라도 사용자의 "추측 금지" 정책에 따라 사용 금지. 본 저장소나 사용자 메시지에 명시되지 않은 endpoint/TR ID는 모두 `<TBD>` 처리.

## 수정 허용 위치

### 신규

- `docs/kis/MISSING_OFFICIAL_VALUES.md`
- `projects/paper-trading/tests/test_missing_official_values_doc.py`
- `docs/ai/jobs/mvp-014-017-bundle/patch.md`

### 수정 가능

- `projects/paper-trading/app/api/routes.py` (`/paper/status` 응답에 `kis_order_dry_run` 한 줄 추가)
- `projects/paper-trading/README.md` (공식 문서값 진행 상황 단락 추가)
- `projects/paper-trading/tests/test_api_paper_status.py` (`kis_order_dry_run` assertion 추가)

### 절대 미수정 (확장 목록)

- `projects/paper-trading/app/broker/kis.py` — KIS endpoint/TR ID/payload 추가 금지, HTTP 라이브러리 import 금지. 본 작업에서 한 줄도 바꾸지 마.
- `projects/paper-trading/app/config.py` — `kis_order_dry_run`은 이미 존재.
- `projects/paper-trading/.env.example` — 이미 `KIS_ORDER_DRY_RUN=true` 포함.
- `projects/paper-trading/app/api/server.py`, `app/main.py`, `app/risk/*`, `app/oms/*`, `app/runtime/*`, `app/strategy/*`, `app/domain/*`, `app/broker/{base,paper,alpaca_paper}.py`.
- 기존 테스트 중 본 작업이 다루지 않는 것: `test_alpaca_paper_stub.py`, `test_broker_interface.py`, `test_config.py`, `test_flow.py`, `test_kill_switch.py`, `test_kis_account_client.py`, `test_kis_auth_client.py`, `test_kis_capabilities.py`, `test_kis_config.py`, `test_kis_http_boundaries.py`, `test_kis_market_data_client.py`, `test_kis_order_preflight.py`, `test_kis_order_request_model.py`, `test_kis_order_response_model.py`, `test_models.py`, `test_oms.py`, `test_paper_broker.py`, `test_paper_runner.py`, `test_risk_engine.py`, `test_strategy_premarket_gap.py`.
- 루트 `.gitignore`, 프로젝트 `.gitignore`.
- `imports/local-mvp/`.
- mvp-001..mvp-013 산출물.

## 구현 작업

`plan.md` §4 코드를 그대로 따른다.

### 1) `docs/kis/MISSING_OFFICIAL_VALUES.md`

`plan.md` §4.2의 마크다운 템플릿을 그대로 사용해서 생성한다. 다음을 반드시 지킨다:

- **모든 endpoint/TR ID/payload 셀은 `<TBD>`** — 실제 값 절대 미포함.
- **모든 `Confirmed` 컬럼은 `no`** — 본 저장소에는 확인된 값이 없으므로.
- 실제 app key/secret/account number 0건.
- `/uapi/`, `/oauth2/`, `paper-api`, `koreainvestment.com` 같은 실제 path/host fragment 0건. 필드 설명은 한국어/영어 일반 설명으로만 적는다("토큰 발급 path", "잔고 조회 endpoint" 등).
- 학습 데이터에서 알고 있는 endpoint를 무심코 적지 마. 사용자가 공식 문서에서 직접 채울 자리.

상위 디렉터리(`docs/kis/`)가 없으면 생성. (`Write` 도구가 부모 디렉터리 없으면 실패할 수 있으니 `mkdir -p docs/kis` 먼저.)

### 2) `app/api/routes.py`

`/paper/status` 핸들러 응답 dict에 한 줄 추가(`kill_switch_engaged` 부근, 자연스러운 위치):

```python
"kis_order_dry_run": bool(settings.kis_order_dry_run),
```

기존 응답 필드(20+개) **모두 보존**. 다른 변경 없음.

### 3) `projects/paper-trading/README.md`

KIS 섹션 뒤(또는 적절한 위치)에 `plan.md` §4.4의 "## 공식 KIS 문서값 진행 상황 (mvp-014)" 단락을 추가. 기존 단락은 변경하지 않는다. MISSING_OFFICIAL_VALUES.md 상대 경로(`../../docs/kis/MISSING_OFFICIAL_VALUES.md`)가 맞는지 확인.

### 4) `tests/test_missing_official_values_doc.py` (신규)

`plan.md` §4.5 코드 그대로. 3개 테스트:

- `test_missing_official_values_file_exists`
- `test_missing_official_values_has_required_sections` — `"OAuth"`, `"해외주식"`, `"모의투자 주문"`, `"Confirmed"` 포함 검증
- `test_missing_official_values_does_not_leak_real_secrets` — 알려진 실 키 prefix(`PSNFD`, `PKID`, `AKIA`, `sk-`, `ghp_`) 부재 + `<TBD>` 존재 + `Confirmed: yes` 부재

### 5) `tests/test_api_paper_status.py` 보정

기존 두 시나리오(`test_paper_status_kis_metadata_fields` / `test_paper_status_with_kis_config_masks_account`)에 추가:

```python
assert "kis_order_dry_run" in body
assert body["kis_order_dry_run"] is True
```

기존 다른 assertion은 모두 보존.

### 6) 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

저장소 루트:

```bash
git diff --stat
git status --short
```

기대: 기존 126 + 신규 5 ≈ 131 tests PASS. compileall exit 0. mvp-014-017-bundle 외 변경 없음(이미 워크트리에 있는 dirty는 본 작업과 무관).

### 7) `docs/ai/jobs/mvp-014-017-bundle/patch.md`

`plan.md` §4.8 템플릿을 그대로 채운다. 핵심:

- §2.2/2.3/2.4에 mvp-015/016/017이 모두 **보류**임을 명확히 표기.
- §2.7 "공식 KIS 문서값 부족으로 실제 HTTP 연결 보류" 단락 필수.
- §3 Safety Confirmation에 KIS endpoint/TR ID 추가 0건, 외부 HTTP 라이브러리 import 0건, raw 값 미노출 명시.
- 실제 KIS 값 절대 인용 금지.

## 완료 정의 (Done)

- `docs/kis/MISSING_OFFICIAL_VALUES.md` 신규, 4섹션 × 필드 30+, 모두 `<TBD>`/`Confirmed: no`, 실제 endpoint/TR ID/key/secret 0건.
- `/paper/status` 응답에 `kis_order_dry_run: bool` 추가, 기존 필드 모두 보존.
- `README.md`에 공식 문서값 진행 상황 단락 추가, MISSING_OFFICIAL_VALUES.md 참조.
- 신규 테스트 3개 PASS, 기존 `test_api_paper_status.py` 보정 PASS.
- `app/broker/kis.py` 0줄 변경.
- `app/config.py` 0줄 변경.
- `.env.example` 0줄 변경.
- 외부 HTTP 라이브러리 import 0건(전 저장소 grep).
- KIS endpoint URL / TR ID / payload 코드/문서 추가 0건.
- 기존 126 테스트 회귀 없음.
- `OrderType.MARKET` 부재 유지.
- Strategy 패키지가 `app.broker.kis*` import 0건 유지.
- `git diff --stat`에 mvp-014-017-bundle 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 8단락 완성, mvp-015/016/017 보류 사유 명확.
- commit/push/merge/deploy 자동화 없음.

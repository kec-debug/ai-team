# Review — mvp-023: Quote 도메인 모델 + KIS quote mapper skeleton + MISSING_MARKET_DATA_VALUES catalog

## Verdict

**APPROVE** (test-isolation 측면의 low-severity plan deviation 1건 노트, 안전 영향 0)

mvp-023 구현이 master roadmap §4 mvp-023 + 중복 방지 규칙(§5)을 충족하고, **pytest 214 PASS** (이전 ≈193 + 신규 21 = 214). KIS endpoint/TR ID/payload 추측 0건, fail-closed 동작 그대로, secrets/credentials 노출 0건. `Quote`는 broker-agnostic 도메인 모델로 mvp-024 candidate scanner에 안전한 입력 인터페이스를 제공.

## 검증된 사실 (직접 확인)

### 1. 코드 / 안전 invariant

1. **`Quote` 도메인 모델 import 격리** (`app/domain/quote.py`):
   - import: `dataclasses.dataclass`, `datetime`, `decimal.Decimal`만(stdlib only).
   - `app.config`, `app.broker.*`, HTTP 라이브러리 import **0건** — 구조적 broker-agnostic.
   - `@dataclass(frozen=True)`로 외부 수정 불가.
   - `source` 필드로 출처 추적(`"kis_paper"`, `"synthetic"` 등) — LLM/Agent 임의 quote 주입 식별 가능.

2. **`kis_quote_mapper.py` 격리** (`app/broker/kis_quote_mapper.py`):
   - import: `typing.Any`, `app.domain.quote.Quote`만.
   - `app.broker.kis` import **0건** (매퍼는 broker-agnostic).
   - 외부 HTTP 라이브러리 import **0건**.
   - 입력 검증(None / 빈 symbol) 후 `NotImplementedError`로 fail-closed.

3. **금지 패턴 0건** (직접 grep `app/domain/quote.py`, `app/broker/kis_quote_mapper.py`, `docs/kis/MISSING_MARKET_DATA_VALUES.md`):
   - `https?://`, `TR_ID`, `tr_id`, `/uapi/`, `/oauth2/` → 0
   - `import requests` / `import httpx` / `import aiohttp` / `import urllib3` → 0

4. **`MISSING_MARKET_DATA_VALUES.md` 안전한 catalog**:
   - 4개 섹션(현재가 endpoint / Quote 응답 매핑 / 호가단위·거래소 시간 / 시세 종류·권한).
   - 모든 값 `<TBD>`, 모든 Confirmed `no` (`Confirmed: yes` 부재 — 테스트로 검증).
   - 실제 endpoint URL / TR ID / path / key prefix 0건.

5. **`KisMarketDataClient.get_quote` 변경 0건** — 여전히 `NotImplementedError`로 fail-closed. mvp-023 회귀 테스트가 명시적 검증.

6. **`app/broker/kis.py` 본문 변경 0건 by mvp-023** — diff 보고된 +225/-13은 mvp-014-017/018 pre-existing dirty. patch.md §3 명시.

7. **`OrderType.MARKET` 부재 유지**(mvp-023이 도메인 코드 미접촉).

8. **Strategy 패키지가 `app.broker.kis*` import 0건** 유지(grep clean per patch.md §4).

### 2. 테스트 (자체 재실행)

```
전체 suite: 214 passed in 0.44s
```

신규 21개 PASS:
- `tests/test_quote_model.py`: 12개 (happy path / 7개 invariant 거절 / spread_pct / is_stale 2개 / naive now / frozen)
- `tests/test_kis_quote_mapper.py`: 3개 (NotImplementedError / None raw / empty symbol)
- `tests/test_missing_market_data_values_doc.py`: 4개 (존재 / 섹션 / Confirmed yes 부재 / 실 키 부재)
- `tests/test_kis_market_data_client.py`: 1개 추가 (mvp-023 fail-closed 회귀)
- mvp-022 신규 1개도 함께 land (`test_load_settings_reads_env_from_project_dir` 등 mvp-022 잔재)

기존 회귀 0건.

### 3. mvp-024 준비

- `Quote` 모델이 broker-agnostic이라 mvp-024 candidate scanner가:
  - 사용자가 `MISSING_MARKET_DATA_VALUES.md`를 채운 뒤 실제 KIS 시세로 작동, 또는
  - `source="synthetic"` 합성 데이터로 scanner 검증 후 실 데이터 교체 가능.
- `source` 필드로 출처 추적이 가능해 LLM/Agent가 임의 quote를 만들지 못함.

## Findings (severity 순)

### 1. (low — plan deviation) `tests/test_kis_config.py` / `tests/test_api_paper_status.py` 테스트 isolation 수정

- 위치: 두 파일 (codex-task plan에서 "기존 테스트 변경 없음"으로 명시했던 영역).
- 관찰: Codex가 두 파일의 기존 테스트(`test_load_settings_default_paper_and_live_disabled`, `test_paper_status_kis_metadata_fields`)에 `tmp_path` fixture + 빈 `.env` write + `monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)`를 추가. `test_load_settings_works_without_env_file`에는 추가로 `monkeypatch.setattr("app.config.load_dotenv", lambda *args, **kwargs: False)` 추가.
- 사유 (patch.md §2.7): mvp-022가 land된 후 `load_settings()`이 프로젝트의 `.env`를 자동 로드. 사용자 로컬 `.env`에 실제 KIS 값이 있으면 "no KIS config" 가정의 테스트가 환경에 따라 다른 결과를 냄. 테스트 isolation으로 deterministic 동작 보장.
- 영향 평가:
  - **안전 영향 0**: 운영 코드 변경 없음, 테스트만 isolation 강화.
  - **테스트 안정성 + 1**: 로컬 `.env` 존재 여부와 무관하게 결과 일관.
  - **plan-strict 평가**: codex-task가 "기존 테스트 변경 없음"을 명시했으므로 엄격하게는 deviation.
  - **실용 평가**: 필요한 수정. mvp-022 land 후 발생한 문제를 mvp-023이 fix. mvp-019 `.gitignore` 패턴과 유사.
- 권장: 인정하고 통과. 향후 plan 작성 시 "`.env` 자동 로딩 기반 테스트는 항상 tmp_path 격리"를 codex-task 표준 가드로 추가.

### 2. (low — process) `app/broker/kis.py` 등 pre-existing dirty가 워크트리에 누적

- 위치: `git diff --stat`이 `app/broker/kis.py` +225/-13, `app/config.py` +11, `app/api/routes.py` +8, `tests/test_broker_interface.py` +34, 외 다수 보고.
- 관찰: 이전 mvps(mvp-014-017-bundle 이후 commit되지 않은 상태)의 누적 dirty. mvp-023 자체는 patch.md §1의 11개 파일에만 변경. 다른 변경은 모두 pre-existing.
- 영향: 안전 위반 없음. commit 시 staging 한정 필요.
- 권장: 아래 액션 아이템 참고.

### 3. (informational) `tests/test_kis_market_data_client.py` 한 줄 회귀 테스트 추가

- 위치: 끝부분 (`test_kis_get_quote_still_fail_closed_after_mvp023`).
- 관찰: 새 테스트가 `KisMarketDataClient.get_quote("AAPL")`이 `NotImplementedError` raise하는지 검증. plan/codex-task가 허용한 형태(기존 import 패턴 활용).
- 영향: 좋음. mvp-023이 시세 영역에 새 코드를 추가하면서 기존 fail-closed 동작이 우발적으로 변경되지 않았는지 명시적 검증.

## File / line references (요청 review focus + scope)

| Review focus | 위치 | 상태 |
| --- | --- | --- |
| 1. KIS endpoint/TR ID/URL/header/payload/response 추측 0건 | grep `https?://` / `TR_ID` / `/uapi/` / `/oauth2/` 0건 in mvp-023 신규 파일 + MISSING_MARKET_DATA_VALUES.md | ✓ |
| 2. Quote 모델 broker-agnostic | `app/domain/quote.py` import는 stdlib only. `app.config`/`app.broker` import 0건 | ✓ |
| 3. KIS quote mapper가 응답 필드 부재 시 fail-closed | `kis_raw_quote_to_domain`이 `NotImplementedError("KIS quote response field mapping ... official documentation")` | ✓ |
| 4. 누락 공식 KIS market data 값 문서화 | `docs/kis/MISSING_MARKET_DATA_VALUES.md` 4섹션 × 모두 `<TBD>` × `Confirmed: no` | ✓ |
| 5. secrets / app key / app secret / account / token 미노출 | grep 검증 + patch.md §3 + `Quote.source` 추적 + 테스트 fake 값만 | ✓ |
| 6. `.env` Git 미추가 | `.env`, `.env.example`, `.gitignore` 모두 미변경 (patch.md §3) | ✓ |
| 7. live trading 비활성 유지 | 도메인/매퍼 코드는 `Settings.live_trading_enabled`를 건드리지 않음. `load_settings()`의 5+1단 차단 그대로 | ✓ |
| 8. 시장가 주문 차단 유지 | `OrderType.MARKET` 부재 + `ALLOW_MARKET_ORDERS=true` reject 유지 | ✓ |
| 9. Strategy/Agent/LLM이 KIS 직접 호출 금지 | `app/strategy/*`에 `app.broker.kis*` import 0건 (grep) | ✓ |
| 10. OMS/RiskEngine 경계 유지 | mvp-023이 OMS/RiskEngine 코드 미접촉. PaperBroker 활성 broker 그대로 | ✓ |
| 11. 테스트 214 PASS | 자체 재실행 `214 passed in 0.44s` | ✓ |
| 12. Scope stayed within mvp-023 | 신규 파일 7개 + README + 3개 테스트 수정(test_kis_market_data_client 회귀 + test_kis_config/test_api_paper_status isolation) | ✓ (deviation 1건 — Findings #1) |

## Missing tests / residual risk

- 21개 신규 테스트가 도메인 모델 invariants + 매퍼 fail-closed + 문서 검증을 잘 커버.
- 운영 환경 위험: 사용자가 `MISSING_MARKET_DATA_VALUES.md`를 채우지 않은 채 mvp-024 진행 시도 시 후속 mvp가 catch해야 함. mvp-024 plan에 prerequisite check를 두는 것이 좋음.
- `Quote` 모델이 broker-agnostic이라 LLM/Agent가 임의로 `source="kis_paper"` 위장 시 detection 메커니즘은 본 mvp 범위 아님. mvp-024 scanner에서 trusted-source allowlist 도입 후보.
- `.env`에 사용자가 직접 채운 실제 KIS 값이 있어도 본 mvp는 그 값을 사용하는 코드 경로가 없음 — 안전.

## Final checklist (요청 review focus + scope)

- [x] `app/domain/quote.py` 신규 — frozen dataclass, broker-agnostic, app.config/app.broker import 0건.
- [x] `Quote.spread_pct` Decimal 분율 (`(ask-bid)/last`).
- [x] `Quote.is_stale` timezone-aware check 양방향 검증.
- [x] `Quote.__post_init__`이 모든 invariant 검증.
- [x] `app/broker/kis_quote_mapper.py` 신규 — NotImplementedError + 입력 검증.
- [x] `kis_quote_mapper.py`에 KIS URL/TR ID/HTTP 라이브러리 0건.
- [x] `app/broker/kis.py` 본문 변경 0건 (mvp-023 scope).
- [x] `docs/kis/MISSING_MARKET_DATA_VALUES.md` 신규 — 4섹션, `<TBD>` × `Confirmed: no` × 실 endpoint/키 0건.
- [x] `Confirmed: yes` 부재 (테스트로 검증).
- [x] Quote 단위 테스트 12 PASS.
- [x] mapper fail-closed 테스트 3 PASS.
- [x] 문서 검증 테스트 4 PASS.
- [x] `KisMarketDataClient.get_quote` 회귀 테스트 PASS.
- [x] 기존 ≈193 회귀 0건 (총 214 PASS).
- [x] `app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/config.py`, `app/domain/{enums,orders,market}.py`, `app/broker/{base,paper,alpaca_paper,kis}.py`, `app/oms/`, `app/risk/`, `app/strategy/`, `app/runtime/`, `app/portfolio/`, `app/session/`, `app/reports/`, `app/static/`, `.env`, `.env.example`, 프로젝트/루트 `.gitignore` 변경 0건 (mvp-023 scope).
- [x] mvp-001..mvp-022 산출물 미변경.
- [x] `OrderType.MARKET` 부재 유지.
- [x] live trading + market orders + KIS_ORDER_DRY_RUN 기본값 모두 유지.
- [x] README에 mvp-023 단락 추가, 기존 단락 변경 없음.
- [x] commit/push/merge/deploy 자동화 없음.
- [x] `patch.md` 5섹션 + Implementation Summary 8단락 완성, 보류 사유 명확.
- [ ] **commit staging 한정 — 사람 액션** (Findings #2 pre-existing dirty 격리).
- [ ] **`docs/ai/MASTER_TRADING_ROADMAP.md`에 mvp-023 완료 표시 (선택)** — roadmap 문서 자체는 사람이 관리.

## 사람에게 남기는 액션 아이템

1. **mvp-023 commit staging 한정** (필수):

   ```bash
   cd /root/ai-dev-center/projects/ai-team
   git add projects/paper-trading/app/domain/quote.py \
           projects/paper-trading/app/broker/kis_quote_mapper.py \
           docs/kis/MISSING_MARKET_DATA_VALUES.md \
           projects/paper-trading/tests/test_quote_model.py \
           projects/paper-trading/tests/test_kis_quote_mapper.py \
           projects/paper-trading/tests/test_missing_market_data_values_doc.py \
           projects/paper-trading/tests/test_kis_market_data_client.py \
           projects/paper-trading/tests/test_kis_config.py \
           projects/paper-trading/tests/test_api_paper_status.py \
           projects/paper-trading/README.md \
           docs/ai/jobs/mvp-023/
   git diff --cached --stat
   ```

   `app/broker/kis.py` (+225) 등 mvp-021/mvp-022 pre-existing dirty는 별도 commit으로 분리. mvp-023 변경에는 mvp-022 잔재(`test_kis_config.py`의 mvp-022 신규 테스트)도 자연스럽게 포함될 수 있음 — staging 시 `--patch` 또는 `git add -p`로 mvp-023 라인만 골라낼 수도 있고, 그대로 묶어 한 commit으로 처리해도 안전.

2. **commit/push/merge/deploy는 사람이 직접.** 본 작업은 자동화하지 않는다.

3. **다음 단계 — mvp-024 (master roadmap §4)**:
   - 목표: 실제 시세 기반 종목 후보 생성.
   - 입력 인터페이스: 본 mvp-023의 `Quote` 도메인 모델.
   - 시작 권고: 사용자가 `docs/kis/MISSING_MARKET_DATA_VALUES.md`의 `<TBD>` 항목을 채우면 실제 KIS 시세 연결로 진행 가능. 채우기 전이라면 `source="synthetic"` mock 데이터로 candidate scanner 구현 → scanner 로직 검증 → KIS 데이터 도착 시 source만 교체.
   - **prerequisite check**: mvp-024 plan에 "MISSING_MARKET_DATA_VALUES.md `<TBD>` 잔존 시 실제 HTTP 호출 분기는 NotImplementedError 유지" 가드 명시 권장.

4. **`docs/ai/MASTER_TRADING_ROADMAP.md` 업데이트 (선택)**: §2.5 "dry-run / 리포트" 섹션에 "Quote 도메인 모델(mvp-023)" 한 줄 추가, "현재 한계" 섹션의 "실제 시세 데이터가 없으므로 candidates_seen=0"은 mvp-024 land 전까지 유지.

5. **MISSING_MARKET_DATA_VALUES.md 채우기 가이드**: 사용자가 KIS 개발자 포털에서 다음을 확인 후 `<TBD>` → 값 + `Confirmed: yes`로 변경:
   - 모의투자 base URL
   - 현재가 endpoint path + TR ID
   - Quote 응답 필드 이름(last/bid/ask/volume/timestamp)
   - 거래소 코드 + 호가단위 + timezone
   - 실시간/지연 시세 권한 + rate limit

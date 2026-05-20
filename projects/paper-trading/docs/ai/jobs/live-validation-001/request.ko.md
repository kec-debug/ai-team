# 작업 ID
live-validation-001

# 작업명
최종 UX / 운영 안정화 및 live validation 준비

paper trading 시스템은 현재 내부 paper engine, KIS 인증/시세/계좌/주문 경계, 대시보드, dry-run, 리포트, e2e 테스트까지 갖추었다.

paper-ux-001에서는 초보자가 보기 쉬운 한국어 대시보드와 모의 주문 실행 UX가 추가되었다.

이번 작업은 실거래를 시작하는 작업이 아니다.

목표는 최종 운영 안정화와 live validation 준비 상태를 만드는 것이다.

즉, 사용자가 나중에 소액 live validation을 검토할 수 있도록 필요한 안전 점검, preflight, arm/disarm UX, kill switch, 운영 체크리스트를 준비한다.

## 목표

- 대시보드에 live validation 준비 상태를 표시한다.
- live trading은 계속 비활성 상태로 유지한다.
- 실제 live 주문 버튼은 만들지 않는다.
- live 활성화 버튼은 만들지 않는다.
- 실계좌 주문 전송 코드는 추가하지 않는다.
- paper trading / dry-run / simulation UX는 유지한다.
- 운영자가 현재 시스템이 live validation 준비 상태인지 확인할 수 있게 한다.
- 최종 preflight checklist를 만든다.
- kill switch 상태를 명확히 보여준다.
- 위험 상태가 있으면 대시보드에서 빨간색 또는 경고문으로 표시한다.
- 사용자가 실수로 live를 켜지 못하도록 fail-closed 구조를 유지한다.

## 대시보드에 추가할 영역

### 1. Live Validation 준비 상태 카드

아래 항목을 표시한다.

- live_trading_enabled
- trading_mode
- market_orders_allowed
- kis_order_dry_run
- kill_switch_engaged
- broker_type
- kis_config_loaded
- kis_authenticated
- kis_market_data_available
- kis_account_loaded
- kis_order_entry_ready
- live_validation_ready

`live_validation_ready`는 아래 조건을 모두 만족할 때만 true가 될 수 있다.

- TRADING_MODE=paper 또는 validation 전용 safe mode
- LIVE_TRADING_ENABLED=false
- ALLOW_MARKET_ORDERS=false
- KIS_ORDER_DRY_RUN=true
- secret_exposed=false
- kill_switch_engaged=false
- KIS config loaded
- paper e2e 테스트 경로 정상
- recent simulation 또는 dry-run 결과 있음

단, 이번 작업에서 live_validation_ready가 true라고 해도 실제 live 주문은 실행되면 안 된다.

### 2. Preflight Checklist

대시보드에 체크리스트를 표시한다.

필수 항목:

- paper mode 확인
- live disabled 확인
- market order disabled 확인
- KIS dry-run enabled 확인
- secret exposed false 확인
- kill switch off 확인
- KIS config loaded 확인
- dashboard simulation 가능 확인
- paper journal 기록 가능 확인
- report 생성 가능 확인
- 1일 손실 제한 설정 확인
- 최대 주문 수 제한 설정 확인
- 허용 종목 whitelist 확인
- 최근 테스트 통과 여부 수동 확인 항목

### 3. 운영 제어 영역

아래 버튼 또는 상태를 제공한다.

- 상태 새로고침
- Kill switch 상태 확인
- Paper simulation 실행
- Dry-run 시작
- Dry-run 중지
- Report 분석
- 최신 리포트 보기

주의:
- 실제 live arm 버튼은 만들지 않는다.
- live trading enabled를 true로 바꾸는 버튼은 만들지 않는다.
- KIS_ORDER_DRY_RUN을 false로 바꾸는 버튼은 만들지 않는다.
- 시장가 주문 허용 버튼은 만들지 않는다.

### 4. 사고 방지 경고 배너

항상 상단에 표시한다.

예:

"현재 시스템은 paper / dry-run 전용입니다. live trading은 비활성화되어 있으며, 실제 주문은 전송되지 않습니다."

위험 상태가 감지되면 더 강하게 표시한다.

예:

- live_trading_enabled=true 감지 시: "위험: live trading 값이 true입니다. 주문 기능은 차단되어야 합니다."
- market_orders_allowed=true 감지 시: "위험: 시장가 주문 허용 값이 true입니다. 시스템은 fail-closed 해야 합니다."
- secret_exposed=true 감지 시: "위험: secret 노출 가능성이 감지되었습니다."

## API / status 보강

필요하면 read-only endpoint를 추가한다.

예:

- GET /ops/status
- GET /ops/preflight
- GET /ops/checklist

단, 이 endpoint들은 읽기 전용이어야 한다.

허용:
- 상태 조회
- checklist 생성
- 안전 상태 요약
- 최근 paper 결과 요약

금지:
- live 활성화
- real order 실행
- KIS dry-run false 변경
- .env 수정
- secret 출력

## 운영 문서 보강

README에 아래 섹션을 추가한다.

- 초보자용 실행 순서
- 대시보드 접속 방법
- paper simulation 실행 방법
- dry-run 실행 방법
- report 확인 방법
- live validation 전에 반드시 확인할 것
- live validation은 아직 실제 실행 단계가 아니라는 설명
- 실거래 전환 전 필요한 조건

## 절대 하지 말 것

- live trading 활성화 금지.
- live order 버튼 추가 금지.
- 실전 주문 endpoint 사용 금지.
- 실계좌 주문 기능 구현 금지.
- KIS_ORDER_DRY_RUN=false로 바꾸는 기능 추가 금지.
- 시장가 주문 허용 금지.
- KIS endpoint, TR ID, payload, header 추측 금지.
- 공식 catalog에 없는 값을 사용하지 말 것.
- 외부 HTTP 라이브러리 추가 금지.
- Strategy, Agent, LLM이 broker를 직접 호출하는 경로 추가 금지.
- executable order를 Agent나 LLM이 생성하게 만들지 말 것.
- OMS 우회 금지.
- RiskEngine 우회 금지.
- `ALLOW_MARKET_ORDERS=true` 허용 금지.
- `OrderType.MARKET` 3중 가드 우회 금지.
- `OrderType.STOP` 도입 금지.
- FX 변환 함수나 환율 상수 도입 금지.
- `.env` 읽기/수정 금지.
- `.env.example`에 실제 값 추가 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호를 코드/문서/테스트/patch에 기록 금지.
- 자동 git commit / push / merge / production deploy 금지.

## 완료 기준

- `/dashboard`에서 live validation 준비 상태를 볼 수 있다.
- `/dashboard`에서 preflight checklist를 볼 수 있다.
- `/dashboard`에서 paper-only / dry-run-only 안전 배너가 유지된다.
- dashboard에서 실제 live 주문을 실행할 수 있는 버튼이 없다.
- dashboard에서 live trading을 true로 바꿀 수 없다.
- dashboard에서 KIS_ORDER_DRY_RUN을 false로 바꿀 수 없다.
- dashboard에서 market order를 허용할 수 없다.
- read-only ops/preflight endpoint가 있다면 secret을 노출하지 않는다.
- live_trading_enabled=true 같은 위험 설정이 감지되면 fail-closed 또는 경고 상태로 표시된다.
- 기존 paper simulation / dry-run / report UX가 깨지지 않는다.
- 기존 테스트가 모두 통과한다.
- 신규 테스트가 추가된다.
- patch.md에 아래 항목을 포함한다.
  - 수정 파일 목록
  - live validation 준비 상태 표시 방식
  - preflight checklist 항목
  - 실제 live 주문이 불가능한 이유
  - secret/account/token 노출 없음 확인
  - live trading 비활성 유지 확인
  - market order guard 유지 확인
  - 테스트 결과
  - Claude 검증 요청 프롬프트
  - Claude 리뷰가 REQUEST CHANGES/BLOCK일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙

## 검증

아래를 실행한다.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
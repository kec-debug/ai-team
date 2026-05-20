# 작업 ID
paper-e2e-001

# 작업명
Paper trading end-to-end 검증 — Quote → Strategy → RiskEngine → OMS → KisBroker/PaperBroker → PaperEngine → Journal/PnL

api-orders-paper-001에서 KIS 모의투자 주문 본문이 구현되었고, 서버 재시작까지 완료되었다.

이제 새 기능을 추가하기 전에 실제 paper trading 흐름이 처음부터 끝까지 끊기지 않는지 검증해야 한다.

이번 작업은 실전 주문 구현이 아니라, 기존 구성요소를 이용해 end-to-end 흐름을 테스트하고 필요한 최소 보강만 하는 작업이다.

## 목표

- synthetic 또는 mock Quote를 주입한다.
- Quote가 전략 입력으로 들어간다.
- 전략이 non-executable OrderIntent를 만든다.
- RiskEngine이 승인/거절을 판단한다.
- OMS가 승인된 intent만 executable paper order로 변환한다.
- BrokerAdapter 경계를 통해 PaperBroker 또는 KisBroker dry-run 경로로 전달된다.
- KIS_ORDER_DRY_RUN=true일 때 실제 HTTP 주문이 나가지 않는다.
- PaperEngine.on_quote()가 fill을 만들고 PaperAccount / Portfolio / PaperJournal을 갱신한다.
- Dashboard 또는 read-only status에서 결과를 확인할 수 있다.
- 이 흐름을 테스트로 검증한다.

## 확인할 end-to-end 흐름

아래 흐름이 실제 테스트에서 검증되어야 한다.

Quote
→ Strategy
→ RiskEngine
→ OMS
→ BrokerAdapter
→ PaperBroker 또는 KisBroker dry-run
→ PaperEngine.on_quote
→ Fill
→ PaperAccount cash update
→ Portfolio position/PnL update
→ PaperJournal 기록
→ dashboard/status 노출

## 구현 범위

- end-to-end 테스트 추가
- 필요한 경우 read-only helper 추가
- 필요한 경우 runtime entrypoint 보강
- 필요한 경우 PaperEngine.submit_intents() 또는 동등 메서드와 기존 dry-run controller 연결 점검
- dashboard/status에 이미 있는 값을 활용해 검증
- 기존 기능을 크게 리팩터링하지 말 것

## 절대 하지 말 것

- live trading 활성화 금지
- 실전 주문 endpoint 사용 금지
- 실계좌 주문 기능 구현 금지
- KIS endpoint, TR ID, payload, header 추측 금지
- KIS 공식 catalog에 없는 값을 사용하지 말 것
- 외부 HTTP 라이브러리 추가 금지
- Strategy, Agent, LLM이 broker를 직접 호출하는 경로 추가 금지
- executable order를 Agent나 LLM이 생성하게 만들지 말 것
- OMS 우회 금지
- RiskEngine 우회 금지
- `ALLOW_MARKET_ORDERS=true` 허용 금지
- `OrderType.MARKET` 3중 가드 우회 금지
- `OrderType.STOP` 도입 금지
- FX 변환 함수나 환율 상수 도입 금지
- `.env` 읽기/수정 금지
- 실제 app key, app secret, access token, Bearer token, 계좌번호를 코드/문서/테스트/patch에 기록 금지
- GUI 파일을 불필요하게 수정하지 말 것
- 자동 git commit / push / merge / production deploy 금지

## 완료 기준

- end-to-end 테스트가 추가된다.
- synthetic Quote 1개 이상으로 전략 후보가 생성된다.
- RiskEngine이 승인/거절을 정상 판단한다.
- RiskEngine 거절 intent는 OMS/Broker로 넘어가지 않는다.
- 승인 intent는 OMS를 통해 paper order로 변환된다.
- KIS_ORDER_DRY_RUN=true에서는 실제 HTTP 주문이 나가지 않는다.
- PaperBroker/PaperEngine 경로에서 fill이 생성된다.
- Fill 이후 cash / position / realized 또는 unrealized PnL / journal이 갱신된다.
- dashboard/status에서 결과 확인에 필요한 read-only 정보가 유지된다.
- secret/account/token이 노출되지 않는다.
- 전체 pytest 회귀 0건.
- 안전 grep clean.
- patch.md에 다음 항목을 포함한다.
  - 수정 파일 목록
  - 검증한 end-to-end 흐름
  - Broker 경계가 유지되는 방식
  - dry-run에서 실제 HTTP 주문이 나가지 않는 근거
  - PaperAccount/Portfolio/Journal 갱신 확인
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
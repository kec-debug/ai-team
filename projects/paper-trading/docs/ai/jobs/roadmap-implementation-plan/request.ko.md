# 작업 ID
roadmap-implementation-plan

# 작업명
남은 paper trading 작업 전체 통합 설계 및 구현 순서 확정

현재 `projects/paper-trading` 프로젝트는 여러 MVP와 paper/api/runtime 작업을 거치면서 많은 기능이 구현되었다.

하지만 지금까지 작업이 너무 잘게 쪼개져서 다음 문제가 생겼다.

- 같은 기능을 다시 설계하거나 다시 구현하려는 상황이 반복된다.
- 어떤 작업이 완료됐고 어떤 작업이 남았는지 헷갈린다.
- KIS 문서값이 필요한 작업과 실제 구현 가능한 작업이 섞인다.
- GUI에서 한국어 요청을 넣으면 작업이 잘못된 경로로 가거나 중복될 때가 있다.
- Codex 구현 후 Claude 검증, 다시 Codex 수정으로 이어지는 흐름이 매번 수동으로 꼬인다.

이제는 남은 7개 작업을 따로따로 즉흥적으로 진행하지 말고, 먼저 전체 설계를 한 번에 정리한 뒤 그 설계 기준으로 구현을 진행하고 싶다.

## 현재 남은 큰 단계

현재 남은 단계는 아래 7개로 본다.

1. `KIS_3`
   - KIS 미체결 / 체결 / 주문상태 조회 공식 문서값 catalog 보강

2. `api-orders-paper-003-query`
   - KIS 미체결 / 체결 / 주문상태 조회 구현

3. `runtime-002`
   - 실제 Quote → Strategy → RiskEngine → OMS → PaperEngine 자동 연결

4. `paper-002`
   - partial fill 다중 시퀀스 / 슬리피지 / market impact 강화

5. `strategy-002`
   - 두 번째 paper 전략 추가

6. `runtime-soak-001`
   - 장시간 paper trading 검증

7. `live-validation-001`
   - 소액 live validation 준비

## 이번 작업 목표

이번 작업은 코드 구현이 아니다.

Claude는 전체 구조를 먼저 분석하고, 남은 7개 작업을 어떻게 묶고 어떤 순서로 구현해야 하는지 설계해줘.

목표는 다음과 같다.

- 지금까지 완료된 작업과 남은 작업을 정확히 구분한다.
- 이미 완료한 작업을 다시 만들지 않게 한다.
- 남은 7개 작업의 의존관계를 정리한다.
- 어떤 작업은 반드시 먼저 해야 하는지 정한다.
- 어떤 작업은 병렬 또는 묶음으로 처리 가능한지 판단한다.
- 어떤 작업은 KIS 공식 문서값 없이는 BLOCKED인지 표시한다.
- 어떤 작업은 지금 바로 Codex 구현 가능한지 표시한다.
- 실제 구현은 너무 큰 단일 job이 아니라, 리뷰 가능한 묶음으로 나눈다.
- 각 묶음별 Codex 작업 범위와 완료 기준을 정의한다.
- 다음에 실제로 실행할 첫 번째 Codex job을 추천한다.

## 반드시 읽을 문서

Claude는 아래 문서를 먼저 읽고 판단해줘.

- `docs/ai/ROADMAP_STATUS.md`
- `docs/ai/MASTER_TRADING_ROADMAP.md`
- `docs/ai/AI_TEAM_REQUEST_GENERATOR_BRIEF.md`
- `docs/kis/MISSING_MARKET_DATA_VALUES.md`
- `docs/kis/MISSING_OFFICIAL_VALUES.md`
- `projects/paper-trading/docs/ai/jobs/`
- `projects/paper-trading/README.md`

그리고 가능하면 현재 git 상태도 확인해서, 이미 커밋된 것과 dirty 상태를 구분해줘.

## 분석해야 할 내용

### 1. 완료된 작업 목록

아래 항목이 실제로 완료됐는지 확인해줘.

- paper-trading 기본 구조
- dashboard UI
- KIS 설정 로딩
- KIS OAuth
- KIS 시세 Quote 매핑
- KIS 계좌 / 잔고 / 포지션 조회
- KIS 모의 주문 `place_order`
- KIS 모의 주문 `cancel_order` / `replace_order`
- 내부 PaperEngine
- PaperAccount
- PaperJournal
- Fill 모델
- 통화별 cash / PnL
- e2e 테스트
- dashboard에 cash / PnL / fill / journal 노출

### 2. 남은 작업별 상태

아래 7개 작업을 각각 분류해줘.

분류 기준:

- DONE
- READY
- PARTIALLY READY
- BLOCKED-BY-DOCS
- BLOCKED-BY-DESIGN
- SHOULD BE MERGED WITH ANOTHER JOB
- SHOULD BE SPLIT

대상:

- `KIS_3`
- `api-orders-paper-003-query`
- `runtime-002`
- `paper-002`
- `strategy-002`
- `runtime-soak-001`
- `live-validation-001`

### 3. 의존관계

아래 관계를 판단해줘.

- `api-orders-paper-003-query`는 `KIS_3` 없이는 가능한가?
- `runtime-002`는 `api-orders-paper-003-query` 전에 가능한가?
- `paper-002`는 `runtime-002` 전에 가능한가?
- `strategy-002`는 `runtime-002` 전에 가능한가?
- `runtime-soak-001`은 어떤 작업 이후에 해야 하는가?
- `live-validation-001`은 어떤 검증이 끝난 뒤에만 해야 하는가?

### 4. 묶음 구현 가능 여부

남은 작업을 무조건 하나씩 하지 말고, 아래처럼 묶을 수 있는지 판단해줘.

예시:

- Bundle A: KIS query catalog + query implementation
  - `KIS_3`
  - `api-orders-paper-003-query`

- Bundle B: Runtime integration
  - `runtime-002`
  - 필요한 e2e flow

- Bundle C: Paper realism
  - `paper-002`

- Bundle D: Strategy expansion
  - `strategy-002`

- Bundle E: Soak verification
  - `runtime-soak-001`

- Bundle F: Live validation prep
  - `live-validation-001`

단, 한 번에 너무 많은 파일을 건드리거나 1000 LoC가 넘을 것 같으면 분할안을 제시해줘.

### 5. 구현 순서 제안

최종적으로 아래 형식으로 구현 순서를 제안해줘.

```text
Phase 1:
- 목표:
- 포함 작업:
- Codex job ID:
- 예상 수정 파일:
- 테스트 기준:
- 완료 후 다음 단계:

Phase 2:
6. 다음에 실제 실행할 Codex job 추천

이번 작업 끝에 반드시 아래 중 하나를 추천해줘.

바로 실행할 다음 Codex job
아직 Codex를 실행하면 안 되는 이유
먼저 채워야 할 KIS catalog 값
먼저 커밋해야 할 dirty work

그리고 다음 Codex job이 가능하다면, 그 job의 request.ko.md 초안을 작성해줘.

절대 하지 말 것
코드 구현하지 마.
Codex 구현 지시를 여러 개 동시에 만들지 마.
KIS endpoint / TR ID / payload / header / response field를 추측하지 마.
공식 catalog에 없는 값을 사용하는 계획을 세우지 마.
live trading 활성화 계획을 세우지 마.
실전 주문 endpoint 구현 계획을 지금 단계에서 실행 대상으로 두지 마.
Strategy / Agent / LLM이 broker를 직접 호출하는 구조를 허용하지 마.
OMS 우회 구조를 허용하지 마.
RiskEngine 우회 구조를 허용하지 마.
.env를 읽거나 수정하지 마.
실제 app key, app secret, access token, Bearer token, 계좌번호를 문서에 기록하지 마.
자동 git commit / push / merge / production deploy 계획을 만들지 마.
GUI 작업과 backend 작업을 같은 Codex job에 섞지 마.
완료 기준

아래 산출물을 만들어줘.

docs/ai/jobs/roadmap-implementation-plan/plan.md
전체 상태 분석
완료 / 남은 작업 / BLOCKED 작업
의존관계
묶음 구현 가능성
최종 구현 순서
다음에 실행할 단 하나의 job 추천
docs/ai/jobs/roadmap-implementation-plan/request.ko.md
이번 요청 원문 정리
가능하면 docs/ai/ROADMAP_STATUS.md 업데이트 제안
직접 수정하지 않고, 필요한 업데이트 내용을 plan.md에 적어줘.
다음 job이 바로 가능하면 그 job의 request.ko.md 초안
단, 실제 Codex 구현은 아직 하지 않는다.
추가 조건
승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 분석을 시작해.
필요한 경우에만 최소한의 질문을 해.
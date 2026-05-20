# 작업 ID
final-platform-plan

# 작업명
Paper-trading 최종 플랫폼 설계 문서 11 종 (00–10) 생성을 위한 plan + Codex task 작성

본 작업은 design-documentation only. **runtime / broker / OMS / RiskEngine / strategy / KIS / live trading 코드를 일체 수정하지 않는다.** application code 무변동. 모든 산출물은 한국어 design 문서 + 본 plan / codex-task 두 메타 파일.

## 시스템 비전

> "Paper training + agent research + strategy lab + live validation console."

24 시간 운영되는 서비스 / 분석 / 모니터링 / 학습 / 리포팅 플랫폼이다. **24 시간 거래가 일어난다는 의미가 아니다.** 실 paper / live 주문 실행은 항상 session policy → risk engine → OMS → execution guard → broker adapter 경로를 통과한다.

- 기본 동작 모드: paper trading.
- live trading 은 잠긴 상태. 별도의 future safety + manual approval flow 가 명시적으로 완료될 때까지 활성화 금지.

## 핵심 설계 원칙 (변경 불가)

- Paper / live 가 UI, API, runtime, status, permissions, operator workflow 모두에서 명확히 분리.
- Paper training 은 24 시간 학습 / replay / synthetic event / 시장 세션 인식 동작을 지원.
- Live validation 은 별도 console (또는 명확히 분리된 페이지) 에 격리.
- Agent 는 직접 주문 안 함. 데이터 수집 / 분석 / 점수화 / 추천 / **non-executable order intent** 까지만.
- OMS 만 executable order request 를 만든다.
- Strategy → RiskEngine → OMS → BrokerAdapter 경계 무변동.
- Broker API 호출은 broker adapter layer 안에서만.
- KIS endpoint / TR ID / request payload / response field / vendor-specific 값은 검증된 공식 문서 또는 기존 승인된 catalog 에서만 인용. 미확인 값은 TODO 또는 fail-closed boundary 로 표시.
- Paper training, verification, observability, safety 가 live 확장보다 우선.
- 수익 보장 / 거짓 성과 주장 / 과장된 승률 주장 0.

## 산출물 (Codex 가 생성, 한국어)

### 11 design 문서

```
projects/paper-trading/docs/ai/jobs/final-platform-plan/00_current_state.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/01_product_spec.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/02_ui_ux_spec.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/03_paper_training_runtime.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/04_agent_strategy_pipeline.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/05_live_validation_console.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/06_api_data_storage.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/07_risk_safety_observability.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/08_runbook.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/09_implementation_backlog.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/10_acceptance_criteria.md
```

### 메타 파일 (본 turn 의 Claude 가 생성)

```
projects/paper-trading/docs/ai/jobs/final-platform-plan/request.ko.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/plan.md
projects/paper-trading/docs/ai/jobs/final-platform-plan/codex-task.md
```

### 결과 보고 (Codex 가 작성)

```
projects/paper-trading/docs/ai/jobs/final-platform-plan/patch.md
```

## 절대 하지 말 것

- 코드 / 테스트 / `.env` / catalog 본문 / runtime 어떤 파일도 수정.
- 새 KIS endpoint / TR ID / payload / header / response field 추측.
- live trading 활성화 계획 / live arm 실행.
- 자동 git commit / push / merge / deploy.
- 수익 보장 / 거짓 성과 주장.
- 시간 추정 (no time estimate).
- 본 turn 에서 코딩.

## 다음 turn 의 Codex 실행 후 흐름

1. Codex 가 11 개 design 문서 + patch.md 생성.
2. Codex 가 patch.md 의 "Claude 검증 요청 프롬프트" 섹션을 작성.
3. 사용자가 그 프롬프트를 review turn 에 전달.
4. Claude review → APPROVE / REQUEST CHANGES / BLOCK.
5. REQUEST CHANGES / BLOCK 인 경우만 follow-up Codex prompt 사용.

# 04. 검증/학습 20 에이전트

본 문서는 paper 결과, dry-run 결과, journal, fill, report를 분석하는 20개 read-only 역할 모듈을 정의한다. 학습 모듈은 proposal만 만들며 자동 적용은 하지 않는다.

## 공통 안전 규칙

Agent는 Broker가 아니다. OMS만 executable `BrokerOrder`를 만든다. Broker Gateway Service만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

## 공통 typed I/O

| 항목 | 내용 |
| --- | --- |
| Input | `ValidationInput(run_id, orders, fills, journal, strategy_results, market_snapshots)` |
| Output | `ValidationOutput(score, confidence, reasons, blockers, recommendations, trace)` |
| Provider | rule-based 기본, 설명 요약만 LLM optional |
| Fallback | deterministic analyzer |
| Parse status | ok / malformed / timeout |
| Mutation | order 0, broker 0, 자동 parameter 적용 0 |

## 20 모듈 catalog

| # | 한국어 / alias | 소속 서비스 | 책임 | Input typed | Output typed / 다음 모듈 | Score / Confidence | Reasons / Blockers 예시 | Provider / Fallback / Parse | 안전 가드 / 의존 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 51 | 검증 / `ValidationAgent` | Validation & Learning | run 전체 acceptance 판단 | run_summary | validation_verdict -> reports | score/confidence | insufficient_data | rule / deterministic / ok | read-only |
| 52 | 백테스트 / `BacktestAgent` | Validation & Learning | historical replay 설계/결과 해석 | historical_snapshots | backtest_result -> comparison | score | data_gap | rule / deterministic / ok | live 권한 0 |
| 53 | 슬리피지 검증 / `SlippageValidationAgent` | Validation & Learning | fill slippage 분포 검증 | expected_price, fills | slippage_report -> reports | score | excessive_slippage | rule / deterministic / ok | read-only |
| 54 | 스프레드 검증 / `SpreadValidationAgent` | Validation & Learning | spread guard 적정성 확인 | quotes, rejected_orders | spread_report -> reports | score | wide_spread | rule / deterministic / ok | guard 완화 자동화 0 |
| 55 | 체결 현실성 검증 / `FillRealismValidationAgent` | Validation & Learning | volume cap, partial fill 현실성 점검 | fills, volume | fill_realism_report -> reports | score | unrealistic_fill | rule / deterministic / ok | read-only |
| 56 | 매매일지 분석 / `JournalAnalysisAgent` | Validation & Learning | journal events 요약 | events, orders | journal_summary -> daily report | confidence | missing_event | rule / deterministic / malformed | secret scrub |
| 57 | 일일 리포트 / `DailyReportAgent` | Validation & Learning | daily paper summary 작성 | validation_outputs | daily_report -> dashboard | confidence | no_run | rule + LLM optional / deterministic / ok | 성과 과장 금지 |
| 58 | 주간 리포트 / `WeeklyReportAgent` | Validation & Learning | 기간별 추세 요약 | daily_reports | weekly_report -> operator | confidence | insufficient_days | rule + LLM optional / deterministic / ok | 시간 약속 0 |
| 59 | 전략 비교 / `StrategyComparisonAgent` | Validation & Learning | strategy별 결과 비교 | strategy_runs | comparison -> learning | score | incomparable_runs | rule / deterministic / ok | 자동 선택 0 |
| 60 | 전략 성과 분해 / `PerformanceAttributionAgent` | Validation & Learning | P&L 요인 분해 | fills, signals | attribution -> reports | score | attribution_unknown | rule / deterministic / ok | 보장 표현 0 |
| 61 | 실패 원인 분류 / `FailureClassifierAgent` | Validation & Learning | rejection/error 원인 분류 | errors, blockers | failure_classes -> backlog | confidence | unknown_failure | rule + LLM optional / deterministic / malformed | LLM 검증 필요 |
| 62 | 회귀 비교 / `RegressionComparisonAgent` | Validation & Learning | 이전 run과 현재 run 비교 | baseline, current | regression_report -> Ops | score | behavior_changed | rule / deterministic / ok | read-only |
| 63 | 데이터 품질 검증 / `DataQualityValidationAgent` | Validation & Learning | stale/missing/outlier data 탐지 | snapshots | data_quality_report -> Market Data/Ops | score | stale_quote | rule / deterministic / ok | KIS 대체 표현 금지 |
| 64 | 신호 노이즈 분석 / `SignalNoiseAgent` | Validation & Learning | noisy signal과 useful signal 분리 | signals, outcomes | noise_report -> learning | score | high_noise | rule / deterministic / ok | proposal만 |
| 65 | LLM 결과 검증 보조 / `LlmOutputValidationAgent` | Validation & Learning | LLM output schema/risk 검증 | agent_output | llm_validation -> provider fallback | confidence | malformed, policy_block | rule / deterministic / malformed | hard block 해제 0 |
| 66 | 학습 / `LearningAgent` | Validation & Learning | paper 결과 기반 개선 proposal | reports, comparisons | learning_proposal -> operator | confidence | insufficient_evidence | rule + LLM optional / deterministic / ok | 자동 적용 0 |
| 67 | 파라미터 튜닝 추천 / `ParameterTuningAgent` | Validation & Learning | strategy parameter 후보 제안 | learning_proposal | parameter_proposal -> review | score | overfit_risk | rule / deterministic / ok | 수동 승인 필요 |
| 68 | 결정 트리 추출 / `DecisionTreeExtractionAgent` | Validation & Learning | 의사결정 explainability 생성 | signals, outcomes | decision_tree_summary -> reports | confidence | tree_unstable | rule / deterministic / ok | read-only |
| 69 | 가설 검증 / `HypothesisValidationAgent` | Validation & Learning | operator hypothesis 검증 | hypothesis, runs | hypothesis_result -> report | score | sample_too_small | rule / deterministic / ok | 적용 0 |
| 70 | 결과 시각화 / `ResultVisualizationAgent` | Validation & Learning | dashboard/report용 chart spec 생성 | reports | visualization_spec -> UI | confidence | missing_series | rule / deterministic / ok | data only |

## 학습 모듈 제한

`LearningAgent`와 `ParameterTuningAgent`는 추천만 생성한다. config, strategy parameter, risk limit을 자동으로 바꾸지 않는다. 변경은 별도 job, review, 테스트가 필요하다.

## 반복 확인

검증/학습 Agent는 Broker가 아니다. OMS만 executable order를 만든다. Broker Gateway만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

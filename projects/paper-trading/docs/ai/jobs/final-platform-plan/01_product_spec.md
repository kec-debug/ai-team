# 01. Product Spec

본 문서는 최종 플랫폼의 제품 구조를 정의한다. 기준 상태는 `00_current_state.md` 이며, 제품 비전은 "Paper training + agent research + strategy lab + live validation console" 이다.

## 1. Overview Dashboard

| 항목 | 내용 |
| --- | --- |
| 정의 | 전체 시스템 상태, safety, paper runtime, readiness 를 한 화면에서 보는 운영 홈 |
| 운영자 use case | 서버가 안전하게 paper 모드인지 확인 |
| 분석가 use case | 최근 run, report, PnL, block reason 확인 |
| 개발자 use case | endpoint / runtime / error 상태 추적 |
| 구현됨 | `/dashboard`, safety banner, paper status, KIS status, dry-run status |
| 미구현 | incident timeline, heartbeat, reconciliation card |
| 의존 | Paper Training, Reports, Risk / Ops |

## 2. Paper Training

| 항목 | 내용 |
| --- | --- |
| 정의 | paper mode 에서 전략 / risk / OMS / broker fill 을 반복 검증하는 학습 영역 |
| 운영자 use case | dry-run 시작, tick, 중지, report 확인 |
| 분석가 use case | 후보, 거절 사유, fill 품질 분석 |
| 개발자 use case | runtime loop, data source, storage 확장 |
| 구현됨 | `DryRunController`, `PaperEngine`, `PaperBroker`, report analyzer |
| 미구현 | 24시간 service loop, TrainingRun aggregation, replay source |
| 의존 | Strategy Lab, Risk, Reports |

## 3. Agent Research

| 항목 | 내용 |
| --- | --- |
| 정의 | 시장 / 기업 / 재무 / 뉴스 / 리스크 분석을 typed output 으로 만드는 research layer |
| 운영자 use case | agent 결과가 주문 권한이 아님을 확인 |
| 분석가 use case | evidence, confidence, blockers 비교 |
| 개발자 use case | provider, fallback, validation 구현 |
| 구현됨 | 없음 |
| 미구현 | 7 agent, LLM optional provider, trace 저장 |
| 의존 | Strategy Lab, Risk, Reports |

## 4. Strategy Lab

| 항목 | 내용 |
| --- | --- |
| 정의 | 전략 정의, 후보 생성, block reason, backtest 를 관리하는 영역 |
| 운영자 use case | 사용 중인 전략과 safe output 확인 |
| 분석가 use case | 전략별 성능과 blocker 분석 |
| 개발자 use case | 새 strategy 추가와 회귀 테스트 |
| 구현됨 | Premarket Gap, Opening Range Breakout |
| 미구현 | strategy registry UI, backtest endpoint, parameter lab |
| 의존 | Paper Training, Agent Research, Risk |

## 5. Orders / Fills

| 항목 | 내용 |
| --- | --- |
| 정의 | paper order, broker order, fill, journal 을 추적하는 영역 |
| 운영자 use case | 실제 주문이 아닌 paper fill 임을 확인 |
| 분석가 use case | fill price, commission, partial fill, rejection 분석 |
| 개발자 use case | idempotency, state transition, reconciliation 구현 |
| 구현됨 | `/paper/orders`, `/paper/fills`, `PaperJournal` |
| 미구현 | persistent order state table, reconciliation dashboard |
| 의존 | OMS, Broker, Portfolio |

## 6. Portfolio

| 항목 | 내용 |
| --- | --- |
| 정의 | cash, position, realized / unrealized PnL snapshot |
| 운영자 use case | paper 계좌 상태 확인 |
| 분석가 use case | strategy별 exposure 분석 |
| 개발자 use case | snapshot persistence 와 rehydrate |
| 구현됨 | `PaperAccount`, `PortfolioService`, `/paper/positions` |
| 미구현 | persistent snapshots, multi-run comparison |
| 의존 | Orders / Fills, Reports |

## 7. Reports / Analytics

| 항목 | 내용 |
| --- | --- |
| 정의 | dry-run / paper training 결과를 사람이 읽는 보고서와 구조화 데이터로 변환 |
| 운영자 use case | latest report 확인 |
| 분석가 use case | block reason, pass rate, fill quality 분석 |
| 개발자 use case | report schema, export, regression |
| 구현됨 | dry-run analyzer, local report files |
| 미구현 | report index, run comparison, export UI |
| 의존 | Paper Training, Agent Research, Portfolio |

## 8. Live Validation Console

| 항목 | 내용 |
| --- | --- |
| 정의 | live readiness 를 paper dashboard 와 분리해 잠금 상태로 표시하는 console |
| 운영자 use case | live 진입 조건을 read-only 로 점검 |
| 분석가 use case | paper 결과가 live 검토 기준을 만족하는지 확인 |
| 개발자 use case | locked arm/disarm state machine 설계 |
| 구현됨 | `/ops/status`, `/ops/preflight`, readiness banner |
| 미구현 | 분리 console, manual approval, locked arm/disarm |
| 의존 | Risk / Ops, KIS status, Reports |

## 9. Risk / Ops / Settings

| 항목 | 내용 |
| --- | --- |
| 정의 | safety guard, settings, kill switch, readiness, audit 를 관리하는 영역 |
| 운영자 use case | unsafe state 를 빠르게 감지 |
| 분석가 use case | rejection 원인과 guard 영향 분석 |
| 개발자 use case | guard 추가와 observability 구현 |
| 구현됨 | `RiskEngine`, settings guard, `safety_grep.sh`, OPS_AUDIT |
| 미구현 | advanced guard, alert skeleton, incident view |
| 의존 | 모든 실행 영역 |

## 10. Runbook / Incident View

| 항목 | 내용 |
| --- | --- |
| 정의 | 운영 절차, 장애 대응, rollback, 감사 기록 |
| 운영자 use case | 매일 같은 순서로 점검 |
| 분석가 use case | incident 와 report 연결 |
| 개발자 use case | operational acceptance 확인 |
| 구현됨 | `docs/RUNBOOK.md`, `docs/OPS_AUDIT.md` |
| 미구현 | incident UI, audit event persistence |
| 의존 | Risk / Ops, Reports |

## 11. Platform navigation

```text
Overview Dashboard
  -> Paper Training -> Orders / Fills -> Portfolio -> Reports
  -> Agent Research -> Strategy Lab -> Risk / Ops
  -> Live Validation Console (locked)
  -> Runbook / Incident View
```

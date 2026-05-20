# 02. UI / UX Spec

본 문서는 운영용 dashboard 설계를 정의한다. marketing page 가 아니라 반복 운영, 오류 파악, 안전 확인을 위한 작업 화면이다. 기준 구현은 `00_current_state.md` §5 와 `01_product_spec.md` 의 10개 product 영역이다.

## 1. 핵심 UX 원칙

- 첫 화면에서 paper / live 상태가 즉시 보인다.
- safety banner 는 항상 보인다.
- live 영역은 기본 lock 상태다.
- operator 가 실수로 live 를 켜는 버튼은 없다.
- 모든 주문 관련 화면은 paper / live 분리를 명확히 표시한다.
- 초보자는 한국어 문구로 현재 상태와 다음 행동을 이해해야 한다.
- 개발자는 raw JSON 과 correlation id 를 추적할 수 있어야 한다.

## 2. Safety banner

| 상태 | 조건 | 색상 의미 | 문구 방향 |
| --- | --- | --- | --- |
| info | paper-only, dry-run-on, secret safe | 정상 | "현재 시스템은 paper / dry-run 전용입니다" |
| warning | KIS config 불완전, kill switch engaged, auth unavailable | 주의 | "새 주문이 차단됩니다" |
| danger | live enabled, market allowed, secret exposed | 즉시 조치 | "시스템은 fail-closed 해야 합니다" |

## 3. Layout wireframe

```text
┌────────────────────────────────────────────────────────────┐
│ Safety Banner: paper / dry-run / live locked               │
├───────────────┬────────────────────────────────────────────┤
│ Left Nav      │ Main Status Grid                           │
│ - Overview    │ ┌ Safety ┐ ┌ KIS ┐ ┌ Paper Run ┐           │
│ - Paper       │ ┌ Risk   ┐ ┌ OMS ┐ ┌ Broker    ┐           │
│ - Agents      │                                            │
│ - Strategy    │ Selected workspace                         │
│ - Orders      │ - details                                  │
│ - Portfolio   │ - blockers                                 │
│ - Reports     │ - raw JSON                                 │
│ - Live Locked │                                            │
│ - Risk / Ops  │                                            │
│ - Runbook     │                                            │
├───────────────┴────────────────────────────────────────────┤
│ Footer: build info / last refresh / active run id           │
└────────────────────────────────────────────────────────────┘
```

## 4. 상태 표시

| 항목 | 표시 방식 | 사용자 의미 |
| --- | --- | --- |
| `trading_mode` | badge | paper 인지 확인 |
| `live_trading_enabled` | red/green status | false 여야 정상 |
| `KIS_ORDER_DRY_RUN` | lock badge | true 여야 안전 |
| `secret_exposed` | danger only | true 면 운영 중지 |
| kill switch | visible switch status only | on 이면 주문 차단 |
| session | card | 주문 가능 window 확인 |

## 5. Paper Training 화면

- start / stop / status / history 를 한 영역에 배치.
- 현재 run id, started_at, last_tick_at, ticks_total 표시.
- candidates_seen, blocked, passed, orders_created, rejected, errors 표시.
- history 는 TrainingRun 도입 전에는 report file 기준.

## 6. Agent 분석 결과 화면

| 필드 | 표시 |
| --- | --- |
| evidence | 근거 목록 |
| confidence | 0~1 scale badge |
| blockers | 빨간 목록 |
| trace | 단계별 접힘 영역 |
| provider_used | rule-based / LLM provider |
| fallback_used | true/false |
| parse_status | valid / malformed / blocked |

Agent 는 주문 버튼을 갖지 않는다.

## 7. Strategy 결과 화면

- candidate symbol / session / quote age / spread 표시.
- entry / exit 후보는 non-executable 으로 표시.
- block reason 을 한국어로 보여준다.
- mock order preview 는 RiskEngine 전 단계와 후 단계를 분리한다.

## 8. Risk / Session / Market guard 가시성

| guard | UI 표시 |
| --- | --- |
| stale quote | quote age, max age, blocked 여부 |
| spread guard | current spread, threshold, blocked 여부 |
| session guard | current session, allowed action |
| risk block | reason, threshold, input value |
| kill switch | global banner + status card |

## 9. Orders / fills / journal / PnL

- order state timeline: created -> risk_checked -> OMS accepted -> broker accepted -> filled/rejected.
- fills: price, quantity, commission, currency, time.
- journal: recent orders, rejected orders, reason.
- portfolio: cash by currency, positions, realized / unrealized PnL.

## 10. Live area lock

Live Validation Console 은 별도 nav item 이지만 default locked 이다. 버튼은 status check 와 read-only preflight 만 제공한다. arm/disarm 은 future design 의 locked state machine 으로만 문서화하며 현재 UI 에서 실행하지 않는다.

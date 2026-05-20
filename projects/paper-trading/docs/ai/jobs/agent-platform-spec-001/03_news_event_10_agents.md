# 03. 뉴스/이벤트 10 에이전트

본 문서는 뉴스와 이벤트를 read-only 신호로 변환하는 10개 역할 모듈을 정의한다. 이 서비스는 주문을 만들지 않고 Strategy Service에 event context만 전달한다.

## 공통 안전 규칙

Agent는 Broker가 아니다. OMS만 executable `BrokerOrder`를 만든다. Broker Gateway Service만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

## 공통 typed I/O

| 항목 | 내용 |
| --- | --- |
| Input | `NewsEventInput(source, headline, body, timestamp, symbol_hint, source_reputation)` |
| Output | `EventSignal(symbols, severity, confidence, reasons, blockers, trace)` |
| Provider | rule-based 기본, 요약에만 LLM optional |
| Fallback | deterministic keyword / source score |
| Parse status | ok / malformed / timeout |
| Mutation | 주문 0, broker 호출 0 |

## 10 모듈 catalog

| # | 한국어 / alias | 소속 서비스 | 책임 | Input typed | Output typed / 다음 모듈 | Score / Confidence | Reasons / Blockers 예시 | Provider / Fallback / Parse | 안전 가드 / 의존 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 41 | 뉴스 수집 / `NewsCollectorAgent` | News & Event | news source에서 raw event 수집 | source, timestamp | raw_news -> classifier | confidence | source_down | rule / deterministic / timeout | read-only |
| 42 | 뉴스 분류 / `NewsClassifierAgent` | News & Event | headline/body를 category로 분류 | raw_news | classified_news -> credibility | confidence | malformed_text | rule + LLM optional / deterministic / malformed | 주문 0 |
| 43 | 뉴스 신뢰도 평가 / `NewsCredibilityAgent` | News & Event | source reliability와 중복 여부 평가 | classified_news | credibility_score -> mapper | score | low_reputation | rule / deterministic / ok | read-only |
| 44 | 공시 모니터 / `DisclosureMonitorAgent` | News & Event | 공시성 이벤트 감지 | disclosure_feed | disclosure_event -> impact | confidence | unsupported_source | rule / deterministic / ok | external write 0 |
| 45 | 실적 발표 모니터 / `EarningsMonitorAgent` | News & Event | earnings calendar와 surprise 후보 감지 | earnings_feed | earnings_event -> impact | score | unconfirmed_release | rule / deterministic / ok | 주문 0 |
| 46 | 거시 이벤트 / `MacroEventAgent` | News & Event | 금리, 지표, 시장 이벤트를 context화 | macro_feed | macro_event -> Strategy | confidence | macro_risk | rule + LLM optional / deterministic / ok | LLM hard block 해제 불가 |
| 47 | 정정/구속력 이벤트 / `BindingEventAgent` | News & Event | 정정, 중단, 규제성 이벤트 감지 | news, disclosure | binding_event -> Ops/Strategy | confidence | halt_like_event | rule / deterministic / ok | blocker만 제안 |
| 48 | 가격 충격 추정 / `EventImpactAgent` | News & Event | event severity와 예상 변동성 보조 추정 | event_signal, quote | event_impact -> Strategy | score | impact_unknown | rule / deterministic / ok | prediction은 보조 |
| 49 | 뉴스 종목 매핑 / `NewsSymbolMapperAgent` | News & Event | event를 symbol list에 매핑 | event, metadata | symbol_event -> alert emitter | confidence | symbol_ambiguous | rule + LLM optional / deterministic / malformed | allowlist 확인 |
| 50 | 이벤트 알림 emit / `EventAlertEmitterAgent` | News & Event | Strategy/Ops로 alert 전달 | symbol_event | alert_event -> Strategy/Ops | confidence | delivery_failed | rule / deterministic / timeout | 주문 0 |

## Strategy Service와의 관계

뉴스/이벤트 모듈은 `EventSignal`과 `AlertEvent`를 보낸다. Strategy Service는 이를 blocker, score adjustment, operator alert로만 사용한다. `OrderIntent` 생성은 `IntentEmitterAgent` 이후 OMS 경계를 거쳐야 한다.

## 반복 확인

뉴스/이벤트 Agent는 Broker가 아니다. OMS만 executable order를 만든다. Broker Gateway만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

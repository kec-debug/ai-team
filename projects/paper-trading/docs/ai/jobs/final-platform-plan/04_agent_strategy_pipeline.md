# 04. Agent / Strategy Pipeline

본 문서는 Agent research 와 Strategy runtime 을 하나의 안전 pipeline 으로 합치는 설계를 정의한다. 기준 안전 원칙은 `00_current_state.md` §8 이며, Agent 와 LLM 은 broker 를 직접 호출하지 않는다.

## 1. Pipeline

```text
Universe -> 7 Agent enrichment -> RiskAnalysis hard block -> Recommendation
   -> Strategy candidate -> RiskEngine verdict -> OMS order request
   -> BrokerAdapter (paper or locked live)
```

## 2. 공통 Agent output 계약

| 필드 | 의미 |
| --- | --- |
| `score` | 정량 점수, 단독 주문 권한 없음 |
| `confidence` | 근거 신뢰도 |
| `reasons` | 긍정 근거 |
| `blockers` | 차단 근거 |
| `metadata` | source, timestamp, provider |
| `execution_trace` | 단계별 입력/출력 요약 |
| `provider_used` | deterministic / LLM |
| `fallback_used` | fallback 여부 |
| `parse_status` | valid / malformed / blocked |

## 3. Agent catalog

### 3.1 MarketResearchAgent

| 항목 | 내용 |
| --- | --- |
| Input | universe, quote snapshot, session, volume context |
| Output | market regime score, liquidity reason, blockers |
| Provider | rule-based default + optional LLM summary |
| Fallback | quote-only deterministic summary |
| Validation | typed score / blockers required |
| Risk block authority | LLM 단독 해제 불가 |

### 3.2 CompanyOverviewAgent

| 항목 | 내용 |
| --- | --- |
| Input | symbol, company profile source |
| Output | business overview, sector, quality notes |
| Provider | deterministic profile source + optional LLM |
| Fallback | cached profile / unknown block |
| Validation | source required |
| Risk block authority | 없음 |

### 3.3 FinancialAnalysisAgent

| 항목 | 내용 |
| --- | --- |
| Input | financial metrics snapshot |
| Output | financial score, red flags, metadata |
| Provider | rule-based metrics |
| Fallback | insufficient-data blocker |
| Validation | numeric ranges |
| Risk block authority | hard blocker 제안 가능, 해제 불가 |

### 3.4 IndustryModelAgent

| 항목 | 내용 |
| --- | --- |
| Input | sector, peers, macro tags |
| Output | industry strength, peer comparison |
| Provider | deterministic model |
| Fallback | sector-only summary |
| Validation | peer data optional, sector required |
| Risk block authority | 없음 |

### 3.5 NewsAgent

| 항목 | 내용 |
| --- | --- |
| Input | news events, timestamp, source |
| Output | sentiment, event risk, blockers |
| Provider | deterministic keyword model + optional LLM |
| Fallback | event list summary |
| Validation | timestamp and source required |
| Risk block authority | event blocker 제안 가능 |

### 3.6 RiskAnalysisAgent

| 항목 | 내용 |
| --- | --- |
| Input | quote, position, portfolio, agent outputs |
| Output | hard blockers, risk notes |
| Provider | deterministic hard rule |
| Fallback | block on uncertainty |
| Validation | blockers explicit |
| Risk block authority | hard block 적용 가능, LLM 해제 불가 |

### 3.7 InvestmentRecommendationAgent

| 항목 | 내용 |
| --- | --- |
| Input | enriched context, risk blockers |
| Output | trade idea, non-executable `OrderIntent` candidate |
| Provider | rule-based default + optional LLM rationale |
| Fallback | no recommendation |
| Validation | non-executable only |
| Risk block authority | hard block 있으면 recommendation 금지 |

## 4. LLM provider design

- default provider 는 rule-based / deterministic.
- LLM 은 optional.
- LLM failure 는 deterministic fallback 으로 전환.
- malformed output 은 validation block.
- LLM 은 hard risk block 을 해제할 수 없다.
- prompt template 은 본 design 범위 밖이다.

> **TODO**: Agent 별 prompt template 과 provider config 는 future job 에서 작성한다.

## 5. Strategy boundary

- Strategy 는 broker 를 직접 import 하지 않는다.
- Strategy 는 candidate 또는 non-executable intent 까지만 생성한다.
- `RiskEngine` verdict 전에는 executable order 가 없다.
- `OMS` 만 executable order request 를 만든다.

## 6. Trace / audit

각 Agent 실행은 `AgentTrace` 로 기록한다. trace 는 provider, fallback, parse_status, blockers, correlation_id 를 포함한다. 이 데이터는 `06_api_data_storage.md` 의 storage 설계와 연결된다.

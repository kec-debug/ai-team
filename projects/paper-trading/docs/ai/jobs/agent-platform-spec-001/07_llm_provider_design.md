# 07. LLM Provider Design

본 문서는 agent platform에서 LLM을 optional provider로 쓰는 방법을 정의한다. 기본 동작은 deterministic이며, LLM 실패 또는 malformed output은 risk를 완화하지 않고 fallback으로 처리한다.

## 안전 invariant

Agent는 Broker가 아니다. OMS만 executable `BrokerOrder`를 만든다. Broker Gateway Service만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

## Provider 추상화

`LLMProvider`는 실행 코드가 아니라 설계 contract다.

```text
LLMProvider pseudocode:
  name
  classify_or_summarize(input, schema, timeout, cost_limit)
  returns provider_result(text_or_json, trace)
```

구현 후보:

| Provider | 상태 | 역할 |
| --- | --- | --- |
| `DeterministicProvider` | default | rule, regex, score table, fixed fallback |
| `OpenAIProvider` | optional abstraction | SDK import 없이 interface만 설계 |
| `AnthropicProvider` | optional abstraction | SDK import 없이 interface만 설계 |

## fallback chain

```text
Primary optional LLM
  -> schema validation failed?
  -> retry once with stricter instruction
  -> secondary optional LLM if configured
  -> DeterministicProvider
  -> parse_status = malformed or timeout
```

Fallback이 발생해도 hard blocker는 유지된다. `RiskEngine`이 거절한 주문을 LLM rationale로 승인할 수 없다.

## Pydantic validation 원칙

각 agent output은 typed schema를 통과해야 한다. 필수 필드 누락, 알 수 없는 enum, score 범위 초과, credential-like text 포함 시 malformed로 기록한다.

| 검증 | 실패 처리 |
| --- | --- |
| required field | retry once, then deterministic |
| score 0.0~1.0 outside | malformed |
| blocker 제거 시도 | policy_block |
| credential-like text | secret_block |
| executable order field | reject, AgentOutput만 허용 |

## Retry / timeout / cost-rate

| 항목 | 원칙 |
| --- | --- |
| retry | malformed일 때 1회 |
| timeout | 짧은 bounded timeout, 초과 시 deterministic |
| cost-rate | provider별 budget counter 기록 |
| failure | trading 권한 상승 없음 |

## secret 격리

Agent code와 LLM prompt에는 raw app key, secret, account number, access token이 들어가지 않는다. Ops & Security Service의 `SecretManagementAgent`가 서비스 identity를 검증하고, Broker Gateway Service만 필요한 credential을 받는다. LLM provider는 KIS credential을 받지 않는다.

## AgentTrace 필드

| 필드 | 의미 |
| --- | --- |
| `provider_used` | deterministic / provider alias |
| `fallback_used` | true/false |
| `parse_status` | ok / malformed / timeout / policy_block |
| `duration_ms` | bounded duration |
| `cost_units` | provider cost accounting |
| `validation_errors` | schema error 요약 |
| `correlation_id` | service message 추적 |

## 적용 대상

LLM optional 대상은 뉴스 분류, 뉴스 요약, 산업 설명, 실패 원인 설명, 일일/주간 리포트 서술처럼 read-only 해석 영역이다. 가격 산정, risk hard block, OMS 승인, Broker Gateway 호출은 LLM 대상이 아니다.

## 반복 확인

LLM provider를 써도 Agent는 Broker가 아니다. OMS만 executable order를 만든다. Broker Gateway만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

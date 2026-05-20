# 10. Acceptance Criteria

본 문서는 final-platform-plan design 자체의 완료 기준과 후속 job 공통 검수 기준을 정의한다.

## 1. 본 design 의 acceptance

| 항목 | 기준 |
| --- | --- |
| 파일 수 | `00_current_state.md` ~ `10_acceptance_criteria.md` 11개 + `patch.md` |
| 위치 | 모두 `docs/ai/jobs/final-platform-plan/` 안 |
| 언어 | design docs 는 한국어 중심 |
| 운영자 readable | 각 doc 첫 문단에서 목적과 안전 원칙 이해 가능 |
| 개발자 specific | backlog / model / endpoint / guard 를 job 으로 변환 가능 |
| 코드 변경 | application code 0 line |
| 테스트 변경 | tests 0 line |
| scripts 변경 | scripts 0 line |
| KIS 추측 | endpoint / TR ID / payload / response field 추측 0 |
| 성과 주장 | 보장형 수익 표현 / 과장된 승률 주장 0 |
| 시간 추정 | 금지 |
| live activation | 실제 활성화 제안 0 |
| secret | app key / secret / account / token 원문 0 |

## 2. Future job 공통 acceptance

| 항목 | 기준 |
| --- | --- |
| pytest | 전체 PASS, 회귀 0 |
| safety grep | clean (`scripts/safety_grep.sh` 또는 동등) |
| 보호 영역 | `app/broker/kis_http.py` 무변동 unless explicitly approved |
| secret | 노출 0 |
| git | commit / push / merge / deploy 자동화 0 |
| Strategy / Agent | broker 직접 호출 0 |
| OMS / RiskEngine | 우회 0 |
| `OrderType` | `STOP` 미도입, `MARKET` guard 유지 |
| FX | 변환 미도입 unless separate approved FX job |
| Korean docs | 사용자-대면 문서는 한국어 |
| KIS catalog | Confirmed 값만 사용, unknown 은 TODO / fail-closed |
| live | default lock + manual approval principle 유지 |

## 3. Review template

각 future review 는 아래를 확인한다.

- 변경 파일이 job scope 와 일치하는가.
- safety guard 가 약화되지 않았는가.
- tests 가 변경된 behavior 를 커버하는가.
- docs 가 operator 에게 잘못된 live 가능성을 암시하지 않는가.
- rollback notes 가 있는가.

## 4. Completion marker

본 design 은 여기서 정의 끝이다. 다음 단계는 `09_implementation_backlog.md` 의 item 중 하나를 선택해 별도 plan / Codex / review cycle 로 시작한다. 이 문서 자체는 live validation 또는 live trading 을 승인하지 않는다.

# 작업 ID
mvp-023

# 작업명
KIS 실제 시세 조회 연결 (또는 공식 문서값 부재 시 fail-closed + missing-values 정리)

현재 시스템은 대시보드, dry-run, report analyzer는 작동하지만 실제 시장 데이터가 없어서 `candidates_seen=0` 상태다.

목표:
KIS Open API 공식 문서값이 확인되는 범위에서 미국주식/해외주식 실제 시세 조회를 연결하고, 전략 후보 생성(mvp-024)의 입력 데이터로 사용할 수 있게 Quote 도메인 모델과 boundary를 준비한다.

중요:
- KIS endpoint/TR ID/payload를 추측하지 마.
- 공식 문서값이 없으면 실제 HTTP 구현하지 말고 `docs/kis/MISSING_MARKET_DATA_VALUES.md`에 필요한 값을 정리해.
- live trading은 계속 비활성.
- 시장가 주문 금지.
- 실주문 기능 건드리지 마.
- Strategy가 KIS 직접 호출하지 마.
- BrokerAdapter/MarketDataClient 경계를 유지해.
- secret/account/token 노출 금지.

완료 기준:
- `get_quote(symbol)` 또는 동등한 quote 조회 경계가 명확하다.
- 공식 문서값이 있으면 실제 HTTP 연결.
- 공식 문서값이 없으면 fail-closed + missing docs.
- Quote 모델에 `symbol`, `last`, `bid`, `ask`, `volume`, `timestamp`, `is_stale` 여부가 있다.
- spread 계산 가능 (`spread_pct` property 또는 helper).
- 테스트 통과.
- 다음 mvp-024에서 candidate scanner가 이 Quote를 사용할 수 있다.

추가 조건:
- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
- 필요한 경우에만 최소한의 질문을 해.

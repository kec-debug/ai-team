# Paper Trading OPS 감사 보고서

이 문서는 현재 paper trading 운영 안전 상태를 점검하기 위한 감사 기록입니다. 본 문서는 live trading 진입을 승인하지 않습니다.

## 1. 현재 안전 상태 요약

- 기본 모드: paper trading.
- live trading: 기본 비활성.
- market order: 기본 비활성.
- KIS order dry-run: 기본 활성.
- kill switch: 운영 기준에서는 off 상태를 확인해야 함.
- dashboard / ops endpoint: read-only 상태 확인 중심.
- paper simulation: 내부 PaperBroker / PaperEngine 경로만 사용.

## 2. 6 단 live trading 차단 가드

1. `Settings` 기본값은 paper trading과 live disabled를 유지한다.
2. `load_settings()`는 live trading 활성 환경을 fail-closed로 거절한다.
3. `RiskEngine.evaluate`는 paper mode와 live disabled 조건을 검사한다.
4. `OMS.place`는 live trading enabled 상태를 거절한다.
5. live 주문 endpoint는 제공되지 않고, paper simulation endpoint만 존재한다.
6. KIS broker는 설정과 preflight가 맞지 않으면 fail-closed하며 catalog 확인 범위 밖 동작을 하지 않는다.

## 3. 3중 market order 가드

1. `ALLOW_MARKET_ORDERS=true`는 설정 로딩 단계에서 거절된다.
2. `RiskEngine`은 paper market order 허용값이 없으면 `OrderType.MARKET`을 거절한다.
3. dashboard와 운영 스크립트는 시장가 허용 토글이나 live 주문 버튼을 제공하지 않는다.

## 4. KIS 안전 경계

- catalog 확인 값만 구현 범위에 사용한다.
- KIS 관련 확장은 확인된 catalog section을 근거로만 진행한다.
- `KIS_ORDER_DRY_RUN=true`가 기본 운영 기준이다.
- 주문 request preflight와 response sanitization을 유지한다.
- 응답과 문서에는 app key, app secret, access token, Bearer token, raw account number를 기록하지 않는다.
- KIS query/order 관련 세부 catalog 출처는 기존 catalog 문서와 job patch를 따른다. 예: catalog §4.7.1.

## 5. Strategy / Agent / LLM 격리

- Strategy는 broker adapter를 직접 import하지 않는다.
- Agent / LLM은 executable broker order를 생성하지 않는다.
- 추천 또는 전략 결과는 non-executable intent로 제한한다.
- executable order는 OMS와 RiskEngine을 통과해야 한다.
- broker-specific API 호출은 broker adapter 안에 머문다.

## 6. 현재 안전 grep 결과

운영자는 다음 명령으로 갱신한다.

```bash
./scripts/safety_grep.sh
```

기대 결과:

```text
===== safety_grep =====

[OK ] external HTTP libs in app/
[OK ] Strategy 가 KIS 직접 import
[OK ] Agent / LLM 의 broker 직접 호출 (app/agent)
[OK ] live trading 활성화 코드
[OK ] market order guard 우회 (allow_market_orders=True)
[OK ] OrderType.STOP 도입
[OK ] FX 변환 함수 도입
[OK ] JWT-style secret 노출 (Bearer eyJ / access_token=eyJ)
[OK ] .env 가 git tracked 인지

===== safety_grep: ALL OK =====
```

## 7. 운영 체크리스트 (매일 paper session 시작 전)

- `./scripts/use_ready_check.sh` 실행 결과가 모두 `[OK ]`인지 확인.
- dashboard 상단 banner가 info level인지 확인.
- `Preflight Checklist` 14개 항목 중 운영자 수동 확인 항목 외 주요 안전 항목이 통과하는지 확인.
- `live_validation_ready`는 참고 신호일 뿐 live 주문 권한이 아님을 확인.
- `secret_exposed=false`인지 확인.
- `live_trading_enabled=false`인지 확인.
- `market_orders_allowed=false`인지 확인.
- `kis_order_dry_run=true`인지 확인.
- `git status --short`의 dirty 파일을 job별로 분류.

## 8. 실거래 전환 전 필요 조건

실거래 전환은 이 audit의 범위가 아닙니다. future job에서 별도 승인, arming 절차, 소액 제한, whitelist, kill switch, rollback, 운영자 수동 승인, 추가 security review를 통과해야 합니다.

현재 운영 결론: paper trading 검증용 tooling만 사용한다. live validation / live trading 진입은 승인하지 않는다.

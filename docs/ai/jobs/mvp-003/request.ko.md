미국주식 자동 페이퍼매매 시스템 구현을 시작해줘.

현재 목표는 실전매매가 아니라 paper trading 자동화다.
live trading은 절대 활성화하지 않는다.

우선 1단계로 아래 기능만 구현해줘.

1. paper trading 전용 기본 설정 구조 만들기
2. live trading 기본 비활성 상태 확인
3. 브로커 인터페이스 구조 점검
4. Alpaca Paper 또는 기존 paper broker adapter 연결 준비
5. RiskEngine 기본 규칙 점검
6. Strategy -> RiskEngine -> OMS -> Broker Adapter 흐름 확인
7. /paper/status 또는 paper 실행 상태 확인 API가 있으면 점검
8. 없는 경우 최소 paper status API 추가
9. 테스트 추가

중요 조건:
- 실계좌 주문 기능은 만들지 마.
- live trading을 true로 바꾸지 마.
- 시장가 주문은 금지해.
- 모든 주문은 RiskEngine을 반드시 통과해야 해.
- OMS를 우회해서 주문하면 안 돼.
- agent나 LLM이 직접 주문하면 안 돼.
- API 키는 .env에서만 읽어야 해.
- 브로커 endpoint를 추측해서 만들지 마.

이번 작업의 목표는 실제 매매 전략 구현 전에,
paper trading 기본 실행 경로가 안전한지 확인하고 부족한 부분을 보완하는 것이다.

완료 후:
- 어떤 파일을 수정했는지
- paper trading 경로가 어떻게 되는지
- live trading이 차단되어 있는지
- 어떤 테스트를 실행했는지
- 다음 단계로 어떤 전략을 구현하면 되는지
정리해줘.
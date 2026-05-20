# Paper Trading 운영 RUNBOOK

이 문서는 paper trading 시스템을 매일 켜서 점검하고 사용할 때의 운영 순서입니다. 본 절차는 paper / dry-run 전용이며 live trading을 켜지 않습니다.

## 1. 시작 전 준비

프로젝트 위치:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
```

가상환경은 프로젝트의 기존 `.venv`를 사용합니다. 직접 테스트를 실행할 때는 다음 형식을 사용합니다.

```bash
.venv/bin/python -m pytest -p no:cacheprovider
```

### PuTTY 터널 설정 (원격 접속 시)

1. PuTTY 의 Connection > SSH > Tunnels 에서:
   - Source port: `8000`
   - Destination: `127.0.0.1:8000`
   - Local 선택, Add 클릭.
2. SSH 접속 후 로컬 브라우저에서 `http://127.0.0.1:8000/dashboard` 접속.

## 2. 서버 명령 cheat sheet

```bash
./scripts/start_server.sh       # 서버 시작 (foreground)
nohup ./scripts/start_server.sh > /tmp/paper.log 2>&1 &   # 백그라운드 시작
./scripts/stop_server.sh        # 서버 정지
./scripts/restart_server.sh     # 재시작
./scripts/status.sh             # 상태 확인 (paper + ops)
./scripts/use_ready_check.sh    # 마스터 점검 (server + smoke + safety + test + git)
```

서버는 기본적으로 안전 환경값을 강제합니다.

- `TRADING_MODE=paper`
- `LIVE_TRADING_ENABLED=false`
- `ALLOW_MARKET_ORDERS=false`
- `KIS_ORDER_DRY_RUN=true`

## 3. Dashboard 접속

브라우저에서 다음 주소를 엽니다.

```text
http://127.0.0.1:8000/dashboard
```

원격 접속이면 위 PuTTY 터널을 먼저 설정합니다.

## 4. Dashboard 에서 확인할 것

- 상단 안전 배너가 paper / dry-run 전용임을 표시하는지 확인합니다.
- `Live Validation 준비 상태`가 read-only 상태값만 보여주는지 확인합니다.
- `Preflight Checklist`의 14개 항목을 확인합니다.
- KIS 상태에서 config/auth/account/market/order readiness를 확인합니다.
- Paper 계좌에서 cash, positions, PnL, fills, rejected orders를 확인합니다.
- Dry-run 상태에서 running, ticks, candidates, orders, errors를 확인합니다.

## 5. Dry-run 운영

대시보드 버튼으로 실행하거나 다음 스크립트를 사용합니다.

```bash
./scripts/start_dry_run.sh
./scripts/tick.sh
./scripts/stop_dry_run.sh
./scripts/analyze.sh
```

최신 분석 리포트는 대시보드의 `최신 리포트 보기` 또는 다음 endpoint로 확인합니다.

```bash
curl http://127.0.0.1:8000/reports/dry-run/latest
```

## 6. Paper simulation 예시

가장 쉬운 방법은 대시보드의 `예시 모의 주문 실행` 버튼입니다. CLI로는 다음 형태를 사용합니다.

```bash
curl -sS -X POST http://127.0.0.1:8000/paper/order/simulate \
  -H "content-type: application/json" \
  -d '{
    "symbol": "AAPL",
    "side": "buy",
    "quantity": 1,
    "order_type": "limit",
    "limit_price": "100",
    "stop_price": null,
    "mock_bid": "99",
    "mock_ask": "100",
    "mock_last": "100",
    "mock_volume": 100,
    "currency": "USD"
  }'
```

이 호출은 PaperBroker / PaperEngine만 사용하며 실제 브로커 주문을 전송하지 않습니다.

## 7. KIS 상태 확인

KIS 상태 점검은 read-only입니다.

```bash
./scripts/status.sh
```

확인 항목:

- `kis_config_loaded`
- `kis_authenticated`
- `account_no_masked`
- `kis_last_error`
- `kis_market_data_available`
- `kis_account_loaded`
- `kis_order_entry_ready`

KIS 설정이 없거나 인증이 실패해도 시스템은 fail-closed 상태로 표시되어야 합니다. 이 문서는 실제 key, secret, account 값을 기록하지 않습니다.

## 8. 테스트 + 안전 grep

일일 운영 전 마스터 점검:

```bash
./scripts/use_ready_check.sh
```

안전 grep만 따로 실행:

```bash
./scripts/safety_grep.sh
```

수동 테스트:

```bash
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

## 9. Git 운영 원칙

```bash
git status --short
```

**`git add -A` 사용 금지.** 변경한 파일을 명시적으로 `git add <path>` 로 추가한다. 본 시스템은 `git commit / push / merge` 를 자동화하지 않는다.

dirty 파일이 여러 job의 잔재라면 logical commit 단위로 분리합니다. commit, push, merge는 사람이 직접 검토 후 실행합니다.

## 10. 문제 해결

### `curl: Failed to connect to 127.0.0.1:8000`

서버가 실행 중이 아닙니다.

```bash
./scripts/start_server.sh
```

### `/dashboard` 가 Not Found

서버 라우트가 올바르게 로드되지 않았을 수 있습니다.

```bash
./scripts/restart_server.sh
```

### JSON 만 보임

브라우저에서 `http://127.0.0.1:8000/dashboard`로 접속합니다. API endpoint를 직접 열면 JSON이 보이는 것이 정상입니다.

### `kis_config_loaded=false`

KIS 설정이 없거나 불완전합니다. 필요한 값은 로컬 `.env`에 사용자가 직접 설정합니다. 이 문서나 로그에 실제 값을 붙여 넣지 않습니다.

### `secret_exposed=true`

CRITICAL입니다. 서버를 중지하고 코드, 로그, 응답에서 raw secret 노출 여부를 보안 검토합니다.

```bash
./scripts/stop_server.sh
```

### `dry-run not running`

```bash
./scripts/start_dry_run.sh
```

### `422 body missing`

POST body JSON 형식이 잘못되었습니다. 위 Paper simulation 예시 또는 `tests/test_paper_e2e_api.py`의 payload 형식을 참고합니다.

### `409 conflict`

이미 실행 중인 상태일 수 있습니다.

```bash
./scripts/stop_dry_run.sh
```

이후 다시 시작합니다.

### `pytest` 가 안 돌아감

```bash
.venv/bin/python -m pytest -p no:cacheprovider
```

모듈 누락이면 `.venv`가 올바르게 준비되었는지 확인합니다.

### `venv` 가 없음

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### `git status dirty`

`git status --short`로 파일을 확인하고, job별 logical commit으로 분리합니다. `git add -A`는 사용하지 않습니다.

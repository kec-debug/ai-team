
## 2026-05-15T06:08:12.368Z — create-job

```
Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-021
```

## 2026-05-15T06:08:12.368Z — save-input

```
Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-021/request.ko.md
```

## 2026-05-15T06:08:12.377Z — claude-plan

```
(no output)
```

## 2026-05-15T06:12:07.405Z — codex-implement

```
(no output)
```

## 2026-05-15T06:19:07.457Z — save-diff

```
diff --git a/docs/ai/jobs/mvp-004/request.ko.md b/docs/ai/jobs/mvp-004/request.ko.md
index 7d9ecf1..dcfaa5c 100644
--- a/docs/ai/jobs/mvp-004/request.ko.md
+++ b/docs/ai/jobs/mvp-004/request.ko.md
@@ -1,10 +1,74 @@
-# 작업 요청
+# 작업 ID
+mvp-004
 
-GUI 파이프라인이 Claude 계획 완료 전에 Codex 단계로 넘어가는 문제를 수정한다.
+# 작업명
+AI 개발팀 GUI 화면 배치 개선
 
-Claude 계획 단계는 plan.md와 codex-task.md가 생성되어야 완료된 것으로 본다.
-Codex 구현 단계는 patch.md가 생성되어야 완료된 것으로 본다.
-Claude 리뷰 단계는 review.md가 생성되어야 완료된 것으로 본다.
+현재 AI 개발팀 브라우저 GUI에서 화면 배치가 불편하다.
 
-전체 파이프라인 버튼은 각 단계의 산출물 파일을 확인한 뒤 다음 단계로 넘어가야 한다.
-승인 대기, 차단, 실패 상태가 감지되면 다음 단계로 넘어가면 안 된다.
+문제점:
+1. 파이프라인 상태 영역이 너무 위에 있어서 핵심 제어 버튼과 시선 흐름이 맞지 않는다.
+2. 승인 / 서비스 제어 / 실시간 출력 영역이 아래쪽에 있어 잘 안 보인다.
+3. 작업 설정 칸이 너무 길어서 화면을 많이 차지한다.
+4. 실제 작업 중에는 승인 버튼, 서비스 제어, 실시간 출력이 더 중요하므로 위쪽에서 바로 보여야 한다.
+
+원하는 변경사항:
+
+1. “파이프라인 상태” 영역을 “Claude → Codex → Claude 전체 실행” 버튼 아래로 내려줘.
+
+2. 아래 영역들을 상단 쪽으로 올려줘.
+   - 승인 / 계속 진행
+   - 거절
+   - 중단
+   - 서비스 제어
+   - 실시간 출력
+
+3. 작업 설정 영역을 더 짧고 컴팩트하게 만들어줘.
+   - 입력칸 높이를 줄여줘.
+   - 필요하면 접기/펼치기 형태로 만들어줘.
+   - 화면에서 너무 많은 공간을 차지하지 않게 해줘.
+
+4. 화면 우선순위를 아래 순서로 재배치해줘.
+   - 상단: 작업 ID / 작업 요청 입력 / 주요 실행 버튼
+   - 그 아래: 승인 / 서비스 제어 / 실시간 출력
+   - 그 아래: 파이프라인 상태
+   - 그 아래: 작업 설정 / 고급 설정 / 산출물 목록
+
+5. Claude + Codex 2-role 구조는 유지해줘.
+   - Gemini Manager, Claude Architect, Claude Reviewer, Git Shell을 다시 노출하지 마.
+   - Claude 계획 생성
+   - Codex 구현 실행
+   - Claude 리뷰 실행
+   - Claude → Codex → Claude 전체 실행
+   이 버튼 구조는 유지해줘.
+
+6. git status와 git diff는 수동 유틸리티 버튼으로만 유지해줘.
+   - commit, push, merge는 자동화하지 마.
+
+7. 반응형 화면도 깨지지 않게 해줘.
+   - 작은 화면에서도 실시간 출력과 승인 버튼이 잘 보여야 한다.
+
+수정 대상:
+- web/public/index.html
+- web/public/app.js
+- web/public/style.css
+- 필요하면 web/server.js
+- README.md 또는 docs/ai/CLAUDE_CODEX_WORKFLOW.md는 변경 내용이 있으면 최소한만 업데이트
+
+금지:
+- 주식 페이퍼매매 로직은 건드리지 마.
+- secrets, .env, auth, payment, production infra, database migrations는 건드리지 마.
+- 임의 shell 명령 입력 기능은 만들지 마.
+- git commit, push, merge는 자동화하지 마.
+
+검증:
+- node --check web/server.js
+- node --check web/public/app.js
+- git diff --stat
+
+완료 후:
+- 어떤 UI 영역을 어디로 옮겼는지
+- 작업 설정 영역을 어떻게 줄였는지
+- Claude + Codex 구조가 유지되는지
+- 테스트 결과가 무엇인지
+patch.md에 정리해줘.
\ No newline at end of file
diff --git a/projects/paper-trading/README.md b/projects/paper-trading/README.md
index 57e054d..26a621b 100644
--- a/projects/paper-trading/README.md
+++ b/projects/paper-trading/README.md
@@ -237,3 +237,53 @@ curl http://127.0.0.1:8000/reports/dry-run/latest
 - `claude_review_input.md` - Claude/Codex가 전략 개선 plan을 작성할 때 참고할 입력 문서
 
 `reports/`는 프로젝트 `.gitignore`로 무시되므로 분석 산출물도 commit되지 않습니다. 응답/리포트에 KIS app key/secret/account 원문은 포함하지 않으며 `dump_safe` 가드가 credential-like key를 차단합니다.
+
+## 초보자용 실행 방법 (mvp-020)
+
+`scripts/` 아래 helper는 paper trading 안전 기본값을 shell에서 강제합니다. `.env`에 다른 값이 있어도 스크립트 실행 환경에서는 `TRADING_MODE=paper`, `LIVE_TRADING_ENABLED=false`, `ALLOW_MARKET_ORDERS=false`, `KIS_ORDER_DRY_RUN=true`가 우선합니다.
+
+```bash
+cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
+./scripts/start_server.sh
+```
+
+다른 터미널에서:
+
+```bash
+./scripts/status.sh
+./scripts/start_dry_run.sh
+./scripts/tick.sh
+./scripts/analyze.sh
+./scripts/stop_dry_run.sh
+```
+
+한 번에 기본 흐름을 확인하려면:
+
+```bash
+./scripts/smoke_check.sh
+```
+
+| 스크립트 | 설명 |
+| --- | --- |
+| `scripts/start_server.sh` | `127.0.0.1`에서 FastAPI 서버를 실행합니다. |
+| `scripts/status.sh` | `/paper/status`와 `/paper/dry-run/status`를 조회합니다. |
+| `scripts/start_dry_run.sh` | dry-run run을 시작합니다. |
+| `scripts/tick.sh` | dry-run이 멈춰 있으면 먼저 시작하고 빈 snapshot tick을 실행합니다. |
+| `scripts/stop_dry_run.sh` | dry-run run을 정지합니다. |
+| `scripts/analyze.sh` | 최신 dry-run 리포트를 분석하고 `analysis_report.md` 경로를 출력합니다. |
+| `scripts/smoke_check.sh` | status, start, tick, analyze, latest, stop 순서로 빠른 확인을 실행합니다. |
+
+스크립트는 `.env`를 출력하지 않고, KIS app key/secret/account/token 원문을 echo하지 않습니다. 서버 응답도 기존 API의 sanitized 상태값만 표시합니다.
+
+## 브라우저 대시보드 (mvp-021)
+
+서버 실행 후 브라우저에서 `http://127.0.0.1:8000/dashboard`를 열면 paper trading 상태, KIS 상태, dry-run 상태, 최신 분석 리포트를 한 화면에서 확인할 수 있습니다. 대시보드는 동일 origin의 안전 endpoint만 호출하며, live trading 활성화 버튼, 시장가 주문 버튼, 실제 주문 버튼은 제공하지 않습니다.
+
+```bash
+cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
+./scripts/start_server.sh
+# then open:
+# http://127.0.0.1:8000/dashboard
+```
+
+표시되는 credential 관련 값은 서버가 이미 sanitize한 상태 필드와 masked account뿐이며, KIS app key/secret/account/token 원문은 HTML/JS에 포함하지 않습니다.
diff --git a/projects/paper-trading/app/api/routes.py b/projects/paper-trading/app/api/routes.py
index 3de49b2..2ca72bb 100644
--- a/projects/paper-trading/app/api/routes.py
+++ b/projects/paper-trading/app/api/routes.py
@@ -3,6 +3,7 @@ from pathlib import Path
 from typing import Any
 
 from fastapi import APIRouter, HTTPException, Request
+from fastapi.responses import HTMLResponse
 from pydantic import BaseModel
 
 from app.domain.market import StrategyInput
@@ -11,6 +12,8 @@ from app.strategy import STRATEGY_NAMES
 
 router = APIRouter()
 
+_DASHBOARD_HTML_PATH = Path(__file__).resolve().parents[1] / "static" / "dashboard.html"
+
 
 class PaperRunRequest(BaseModel):
     snapshots: list[StrategyInput]
@@ -35,6 +38,11 @@ def healthz() -> dict[str, bool]:
     return {"ok": True}
 
 
+@router.get("/dashboard", response_class=HTMLResponse)
+def dashboard_page() -> HTMLResponse:
+    return HTMLResponse(content=_DASHBOARD_HTML_PATH.read_text(encoding="utf-8"))
+
+
 @router.get("/paper/status")
 def paper_status(request: Request) -> dict[str, Any]:
     settings = request.app.state.settings
diff --git a/projects/paper-trading/app/broker/kis.py b/projects/paper-trading/app/broker/kis.py
index 69265c8..f2477f4 100644
--- a/projects/paper-trading/app/broker/kis.py
+++ b/projects/paper-trading/app/broker/kis.py
@@ -7,7 +7,7 @@ confirmed from official KIS Open API documentation.
 """
 
 from dataclasses import dataclass
-from datetime import datetime, timezone
+from datetime import datetime, timedelta, timezone
 from decimal import Decimal
 from typing import Any
 
@@ -40,6 +40,52 @@ class KisOrderRejectedError(KisError):
         self.reason = reason
 
 
+class KisHttpError(KisError):
+    """Safe wrapper for KIS HTTP failures."""
+
+
+@dataclass(frozen=True)
+class KisPosition:
+    symbol: str
+    quantity: int
+    avg_price: Decimal
+    market_value: Decimal
+
+
+@dataclass(frozen=True)
+class KisCashBalance:
+    currency: str
+    cash: Decimal
+    withdrawable_cash: Decimal
+
+
+@dataclass(frozen=True)
+class KisDryRunPreview:
+    request: "KisOrderRequest"
+    payload_sanitized: dict[str, Any]
+
+
+class KisHttpClient:
+    """HTTP boundary for future KIS calls.
+
+    Endpoint paths, TR IDs, and payload shapes are intentionally absent until
+    verified from official KIS documentation.
+    """
+
+    def __init__(self, settings: Settings, timeout_seconds: float = 5.0, max_retries: int = 1) -> None:
+        self._settings = settings
+        self.timeout_seconds = timeout_seconds
+        self.max_retries = max_retries
+
+    def request(self, method: str, path: str, headers: dict[str, Any] | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
+        raise NotImplementedError(
+            "KIS HTTP request(): official KIS endpoint path, TR ID, headers, and payload are required"
+        )
+
+    def sanitized_preview(self, payload: dict[str, Any] | None) -> dict[str, Any]:
+        return sanitize_kis_response(payload or {}, self._settings)
+
+
 @dataclass(frozen=True)
 class KisOrderRequest:
     """Internal KIS order request model with no raw account number."""
@@ -119,6 +165,27 @@ def sanitize_kis_response(raw: dict[str, Any] | None, settings: Settings) -> dic
     return {key: sanitize_field(key, value) for key, value in raw.items()}
 
 
+def _decimal_from(value: Any) -> Decimal:
+    if value is None or value == "":
+        return Decimal("0")
+    return Decimal(str(value).replace(",", ""))
+
+
+def _int_from(value: Any) -> int:
+    if value is None or value == "":
+        return 0
+    return int(Decimal(str(value).replace(",", "")))
+
+
+def _validate_paper_settings(settings: Settings) -> None:
+    if settings.trading_mode != TradingMode.PAPER:
+        raise KisOrderRejectedError("trading_mode_not_paper")
+    if settings.live_trading_enabled:
+        raise KisOrderRejectedError("live_trading_enabled")
+    if settings.kis_env != "paper":
+        raise KisOrderRejectedError("kis_env_not_paper")
+
+
 def validate_kis_order_request(settings: Settings, broker_order: BrokerOrder) -> None:
     """Pre-flight guards for KIS order paths."""
     if settings.trading_mode != TradingMode.PAPER:
@@ -155,6 +222,7 @@ class KisAuthClient:
         if not settings.kis_app_key or not settings.kis_app_secret:
             raise KisConfigError("KIS_APP_KEY / KIS_APP_SECRET missing in .env")
         self._settings = settings
+        self._http = KisHttpClient(settings)
         self._access_token: str | None = None
         self._expires_at: datetime | None = None
         self._last_error: str | None = None
@@ -177,13 +245,40 @@ class KisAuthClient:
         self._access_token = None
         self._expires_at = None
 
+    def token_expires_at_relative(self) -> str | None:
+        if self._expires_at is None:
+            return None
+        remaining = int((self._expires_at - datetime.now(timezone.utc)).total_seconds())
+        if remaining <= 0:
+            return "expired"
+        return f"in_{remaining}s"
+
+    def _store_token(self, access_token: str, expires_in_seconds: int) -> None:
+        if not access_token:
+            raise KisAuthError("KIS access token missing")
+        self._access_token = access_token
+        self._expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
+        self._last_error = None
+
     def authenticate(self) -> None:
+        try:
+            _validate_paper_settings(self._settings)
+        except KisOrderRejectedError as exc:
+            self._last_error = exc.reason
+            raise KisAuthError(exc.reason) from exc
+        self._last_error = "official_kis_auth_endpoint_required"
         raise NotImplementedError(
             "KIS authenticate(): TODO — confirm OAuth/token endpoint, payload, and response shape "
             "from KIS Open API official documentation. Do not invent endpoints."
         )
 
     def refresh_token(self) -> None:
+        try:
+            _validate_paper_settings(self._settings)
+        except KisOrderRejectedError as exc:
+            self._last_error = exc.reason
+            raise KisAuthError(exc.reason) from exc
+        self._last_error = "official_kis_refresh_endpoint_required"
         raise NotImplementedError(
             "KIS refresh_token(): TODO — confirm refresh endpoint and payload from KIS Open API "
             "official documentation. Do not invent endpoints."
@@ -203,6 +298,8 @@ class KisAccountClient:
         self._settings = settings
         self._auth = auth
         self._account_loaded = False
+        self._positions_loaded = False
+        self._cash_balance_loaded = False
         self._last_error: str | None = None
 
     def __repr__(self) -> str:
@@ -217,24 +314,75 @@ class KisAccountClient:
     def is_loaded(self) -> bool:
         return self._account_loaded
 
+    def positions_loaded(self) -> bool:
+        return self._positions_loaded
+
+    def cash_balance_loaded(self) -> bool:
+        return self._cash_balance_loaded
+
+    def _require_auth(self) -> None:
+        if not self._auth.is_authenticated():
+            self._last_error = "authentication_required"
+            raise KisAuthError("KIS authentication required")
+
     def get_account(self) -> dict[str, Any]:
+        self._require_auth()
+        self._last_error = "official_kis_account_endpoint_required"
         raise NotImplementedError(
             "KIS get_account(): TODO — confirm account endpoint, TR ID, payload, and response shape "
             "from KIS Open API official documentation. Do not invent endpoints."
         )
 
-    def get_positions(self) -> dict[str, int]:
+    def get_positions(self) -> list[KisPosition]:
+        self._require_auth()
+        self._last_error = "official_kis_positions_endpoint_required"
         raise NotImplementedError(
             "KIS get_positions(): TODO — confirm positions endpoint, TR ID, payload, and response shape "
             "from KIS Open API official documentation. Do not invent endpoints."
         )
 
-    def get_cash_balance(self) -> dict[str, Any]:
+    def get_cash_balance(self) -> KisCashBalance:
+        self._require_auth()
+        self._last_error = "official_kis_cash_balance_endpoint_required"
         raise NotImplementedError(
             "KIS get_cash_balance(): TODO — confirm balance endpoint, TR ID, payload, and response shape "
             "from KIS Open API official documentation. Do not invent endpoints."
         )
 
+    def parse_positions_response(self, raw: dict[str, Any]) -> list[KisPosition]:
+        sanitized = sanitize_kis_response(raw, self._settings)
+        rows = sanitized.get("positions") or sanitized.get("output") or []
+        positions: list[KisPosition] = []
+        if isinstance(rows, dict):
+            rows = [rows]
+        for row in rows if isinstance(rows, list) else []:
+            if not isinstance(row, dict):
+                continue
+            symbol = str(row.get("symbol") or row.get("pdno") or row.get("ticker") or "").upper()
+            if not symbol:
+                continue
+            positions.append(
+                KisPosition(
+                    symbol=symbol,
+                    quantity=_int_from(row.get("quantity") or row.get("qty") or row.get("hldg_qty")),
+                    avg_price=_decimal_from(row.get("avg_price") or row.get("pchs_avg_pric")),
+                    market_value=_decimal_from(row.get("market_value") or row.get("evlu_amt")),
+                )
+            )
+        self._positions_loaded = True
+        return positions
+
+    def parse_cash_balance_response(self, raw: dict[str, Any]) -> KisCashBalance:
+        sanitized = sanitize_kis_response(raw, self._settings)
+        source = sanitized.get("cash") if isinstance(sanitized.get("cash"), dict) else sanitized
+        balance = KisCashBalance(
+            currency=str(source.get("currency") or source.get("crcy_cd") or "USD"),
+            cash=_decimal_from(source.get("cash") or source.get("dnca_tot_amt")),
+            withdrawable_cash=_decimal_from(source.get("withdrawable_cash") or source.get("nxdy_excc_amt")),
+        )
+        self._cash_balance_loaded = True
+        return balance
+
     @property
     def last_error(self) -> str | None:
         return self._last_error
@@ -246,31 +394,44 @@ class KisMarketDataClient:
     def __init__(self, settings: Settings, auth: KisAuthClient) -> None:
         self._settings = settings
         self._auth = auth
+        self._http = KisHttpClient(settings)
         self._last_error: str | None = None
 
     def __repr__(self) -> str:
         return "KisMarketDataClient(<disconnected>)"
 
     def get_quote(self, symbol: str) -> dict[str, Any]:
+        self._validate_symbol(symbol)
+        if not self._auth.is_authenticated():
+            self._last_error = "authentication_required"
+            raise KisAuthError("KIS authentication required")
+        self._last_error = "official_kis_quote_endpoint_required"
         raise NotImplementedError(
             "KIS get_quote(): TODO — confirm market data endpoint, TR ID, payload, and response shape "
             "from KIS Open API official documentation. Do not invent endpoints."
         )
 
     def get_last_price(self, symbol: str) -> Any:
-        raise NotImplementedError(
-            "KIS get_last_price(): TODO — confirm market data endpoint, TR ID, payload, and response shape "
-            "from KIS Open API official documentation. Do not invent endpoints."
-        )
+        quote = self.get_quote(symbol)
+        return quote.get("last_price")
 
     def healthcheck_market_data(self) -> dict[str, Any]:
         return {
             "connected": False,
+            "available": False,
             "reason": "skeleton — KIS Open API market data HTTP calls not implemented in this phase",
             "auth_required": True,
             "auth_present": self._auth.is_authenticated(),
+            "last_error": self._last_error,
         }
 
+    def _validate_symbol(self, symbol: str) -> str:
+        normalized = symbol.strip().upper()
+        if not normalized or not normalized.replace(".", "").isalnum():
+            self._last_error = "invalid_symbol"
+            raise KisDataUnavailableError("invalid_symbol")
+        return normalized
+
     @property
     def last_error(self) -> str | None:
         return self._last_error
@@ -304,6 +465,7 @@ class KisBroker:
         self._account = KisAccountClient(settings, self._auth)
         self._market_data = KisMarketDataClient(settings, self._auth)
         self._last_error: str | None = None
+        self._last_order_preview: KisDryRunPreview | None = None
 
     def __repr__(self) -> str:
         return (
@@ -337,7 +499,8 @@ class KisBroker:
         return self._account.get_account()
 
     def get_positions(self) -> dict[str, int]:
-        return self._account.get_positions()
+        positions = self._account.get_positions()
+        return {position.symbol: position.quantity for position in positions}
 
     def get_quote(self, symbol: str) -> dict[str, Any]:
         return self._market_data.get_quote(symbol)
@@ -350,24 +513,29 @@ class KisBroker:
 
     def place_order(self, broker_order: BrokerOrder) -> OrderAck:
         validate_kis_order_request(self._settings, broker_order)
-        self._to_kis_request(broker_order)
+        request = self._to_kis_request(broker_order)
+        if self._settings.kis_order_dry_run:
+            self._last_order_preview = self._dry_run_preview(request)
+            return OrderAck(
+                oms_id=broker_order.oms_id,
+                broker_order_id=None,
+                status="dry_run",
+                mode=self.mode,
+            )
+        self._last_error = "official_kis_order_endpoint_required"
         raise NotImplementedError(
             "KIS place_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard. "
-            "Pre-flight passed but HTTP transmission is intentionally not implemented until KIS Open API "
+            "Pre-flight passed but order endpoint HTTP transmission is intentionally not implemented until KIS Open API "
             "endpoints/TR IDs/payloads are confirmed from official documentation."
         )
 
     def cancel_order(self, broker_order_id: str) -> None:
-        if self._settings.trading_mode != TradingMode.PAPER:
-            raise KisOrderRejectedError("trading_mode_not_paper")
-        if self._settings.live_trading_enabled:
-            raise KisOrderRejectedError("live_trading_enabled")
+        _validate_paper_settings(self._settings)
         if self._settings.allow_market_orders:
             raise KisOrderRejectedError("market_orders_allowed_flag_set")
-        if self._settings.kis_env != "paper":
-            raise KisOrderRejectedError("kis_env_not_paper")
         if self._settings.kill_switch_engaged:
             raise KisOrderRejectedError("kill_switch_engaged")
+        self._last_error = "official_kis_cancel_endpoint_required"
         raise NotImplementedError("KIS cancel_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard.")
 
     def replace_order(self, broker_order_id: str, broker_order: BrokerOrder) -> OrderAck:
@@ -397,6 +565,10 @@ class KisBroker:
             "order_status": False,
         }
 
+    @property
+    def last_order_preview(self) -> KisDryRunPreview | None:
+        return self._last_order_preview
+
     def _idempotency_key_for(self, broker_order: BrokerOrder) -> str:
         return f"kis-paper-{broker_order.oms_id}"
 
@@ -414,6 +586,23 @@ class KisBroker:
             idempotency_key=self._idempotency_key_for(broker_order),
         )
 
+    def _dry_run_preview(self, request: KisOrderRequest) -> KisDryRunPreview:
+        payload = {
+            "symbol": request.symbol,
+            "market": request.market,
+            "side": request.side.value,
+            "quantity": request.quantity,
+            "order_type": request.order_type.value,
+            "limit_price": str(request.limit_price),
+            "account_no": request.account_no_masked,
+            "idempotency_key": request.idempotency_key,
+            "app_key": self._settings.kis_app_key,
+        }
+        return KisDryRunPreview(
+            request=request,
+            payload_sanitized=sanitize_kis_response(payload, self._settings),
+        )
+
     def healthcheck(self) -> dict[str, Any]:
         market = self._market_data.healthcheck_market_data()
         return {
@@ -421,11 +610,15 @@ class KisBroker:
             "environment": self._settings.kis_env,
             "config_loaded": True,
             "authenticated": self._auth.is_authenticated(),
+            "token_expires_at": self._auth.token_expires_at_relative(),
             "account_loaded": self._account.is_loaded(),
+            "positions_loaded": self._account.positions_loaded(),
+            "cash_balance_loaded": self._account.cash_balance_loaded(),
             "market_data": market,
             "last_error": self._last_error,
             "order_execution_implemented": False,
             "order_methods_fail_closed": True,
+            "order_dry_run": self._settings.kis_order_dry_run,
             "capabilities": self.capabilities(),
         }
 
diff --git a/projects/paper-trading/tests/test_broker_interface.py b/projects/paper-trading/tests/test_broker_interface.py
index 09b857f..982052d 100644
--- a/projects/paper-trading/tests/test_broker_interface.py
+++ b/projects/paper-trading/tests/test_broker_interface.py
@@ -9,6 +9,7 @@ from decimal import Decimal
 
 from app.broker.kis import (
     KisAccountClient,
+    KisAuthError,
     KisAuthClient,
     KisBroker,
     KisMarketDataClient,
@@ -110,8 +111,10 @@ def test_kis_place_cancel_replace_not_implemented(settings):
     broker = KisBroker(_configured(settings))
     with pytest.raises(KisOrderRejectedError):
         broker.place_order(_broker_order(quantity=0))
-    with pytest.raises(NotImplementedError):
-        broker.place_order(_broker_order())
+    assert broker.place_order(_broker_order()).status == "dry_run"
+    broker_no_dry_run = KisBroker(replace(_configured(settings), kis_order_dry_run=False))
+    with pytest.raises(NotImplementedError, match="order endpoint"):
+        broker_no_dry_run.place_order(_broker_order())
     with pytest.raises(NotImplementedError):
         broker.cancel_order("x")
     with pytest.raises(NotImplementedError):
@@ -120,28 +123,23 @@ def test_kis_place_cancel_replace_not_implemented(settings):
 
 def test_kis_protocol_methods_delegate_to_not_implemented(settings):
     broker = KisBroker(_configured(settings))
-    with pytest.raises(NotImplementedError):
-        broker.submit(_broker_order())
+    assert broker.submit(_broker_order()).status == "dry_run"
     with pytest.raises(NotImplementedError):
         broker.cancel("x")
     with pytest.raises(NotImplementedError):
         broker.open_orders()
-    with pytest.raises(NotImplementedError):
+    with pytest.raises(KisAuthError, match="authentication required"):
         broker.positions()
 
 
 def test_kis_data_methods_not_implemented(settings):
     broker = KisBroker(_configured(settings))
-    for method, args in (
-        ("authenticate", ()),
-        ("refresh_token", ()),
-        ("get_account", ()),
-        ("get_positions", ()),
-        ("get_open_orders", ()),
-        ("get_quote", ("AAPL",)),
-    ):
+    for method, args in (("authenticate", ()), ("refresh_token", ()), ("get_open_orders", ())):
         with pytest.raises(NotImplementedError, match="TODO"):
             getattr(broker, method)(*args)
+    for method, args in (("get_account", ()), ("get_positions", ()), ("get_quote", ("AAPL",))):
+        with pytest.raises(KisAuthError, match="authentication required"):
+            getattr(broker, method)(*args)
 
 
 def test_kis_broker_has_get_fills_and_get_order_status(settings):
@@ -218,6 +216,16 @@ def test_strategy_package_does_not_import_kis():
         assert not pattern.search(text), f"{path} imports app.broker.kis"
 
 
+def test_agent_package_does_not_import_kis_if_present():
+    root = pathlib.Path(__file__).resolve().parent.parent / "app" / "agents"
+    if not root.exists():
+        return
+    pattern = re.compile(r"\bapp\.broker\.kis\b")
+    for path in root.rglob("*.py"):
+        text = path.read_text(encoding="utf-8")
+        assert not pattern.search(text), f"{path} imports app.broker.kis"
+
+
 def test_kis_module_does_not_import_http_libraries():
     here = pathlib.Path(__file__).resolve().parent.parent / "app" / "broker" / "kis.py"
     text = here.read_text(encoding="utf-8")
diff --git a/projects/paper-trading/tests/test_config.py b/projects/paper-trading/tests/test_config.py
index 6e7190f..44b85b3 100644
--- a/projects/paper-trading/tests/test_config.py
+++ b/projects/paper-trading/tests/test_config.py
@@ -6,9 +6,11 @@ from app.config import load_settings
 def test_load_settings_defaults_to_paper(monkeypatch):
     monkeypatch.delenv("TRADING_MODE", raising=False)
     monkeypatch.delenv("LIVE_TRADING_ENABLED", raising=False)
+    monkeypatch.delenv("KIS_ORDER_DRY_RUN", raising=False)
     settings = load_settings()
     assert settings.trading_mode.value == "paper"
     assert settings.live_trading_enabled is False
+    assert settings.kis_order_dry_run is True
 
 
 def test_load_settings_rejects_live_mode(monkeypatch):
@@ -22,3 +24,11 @@ def test_load_settings_rejects_live_enabled(monkeypatch):
     monkeypatch.setenv("LIVE_TRADING_ENABLED", "true")
     with pytest.raises(ValueError, match="Live trading is disabled"):
         load_settings()
+
+
+def test_load_settings_reads_kis_order_dry_run(monkeypatch):
+    monkeypatch.setenv("TRADING_MODE", "paper")
+    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
+    monkeypatch.setenv("KIS_ORDER_DRY_RUN", "false")
+    settings = load_settings()
+    assert settings.kis_order_dry_run is False
diff --git a/projects/paper-trading/tests/test_kis_account_client.py b/projects/paper-trading/tests/test_kis_account_client.py
index d3cab44..d7405bf 100644
--- a/projects/paper-trading/tests/test_kis_account_client.py
+++ b/projects/paper-trading/tests/test_kis_account_client.py
@@ -2,7 +2,7 @@ from dataclasses import replace
 
 import pytest
 
-from app.broker.kis import KisAccountClient, KisAuthClient, KisConfigError
+from app.broker.kis import KisAccountClient, KisAuthClient, KisAuthError, KisConfigError
 
 
 def _settings(settings, account_no="12345678"):
@@ -44,7 +44,13 @@ def test_account_client_initial_state_not_loaded(settings):
 
 
 def test_account_client_methods_fail_closed(settings):
-    account = KisAccountClient(_settings(settings), _auth(settings))
+    auth = _auth(settings)
+    account = KisAccountClient(_settings(settings), auth)
+    for method in ("get_account", "get_positions", "get_cash_balance"):
+        with pytest.raises(KisAuthError, match="authentication required"):
+            getattr(account, method)()
+
+    auth._store_token("fake-token", 60)
     for method in ("get_account", "get_positions", "get_cash_balance"):
         with pytest.raises(NotImplementedError, match="official documentation"):
             getattr(account, method)()
diff --git a/projects/paper-trading/tests/test_kis_market_data_client.py b/projects/paper-trading/tests/test_kis_market_data_client.py
index e097128..bcbcb6a 100644
--- a/projects/paper-trading/tests/test_kis_market_data_client.py
+++ b/projects/paper-trading/tests/test_kis_market_data_client.py
@@ -2,7 +2,7 @@ from dataclasses import replace
 
 import pytest
 
-from app.broker.kis import KisAuthClient, KisMarketDataClient
+from app.broker.kis import KisAuthClient, KisAuthError, KisMarketDataClient
 
 
 def _settings(settings):
@@ -17,11 +17,17 @@ def _settings(settings):
 
 def _market_data(settings):
     auth = KisAuthClient(_settings(settings))
-    return KisMarketDataClient(_settings(settings), auth)
+    return KisMarketDataClient(_settings(settings), auth), auth
 
 
 def test_market_data_methods_fail_closed(settings):
-    market_data = _market_data(settings)
+    market_data, auth = _market_data(settings)
+    with pytest.raises(KisAuthError, match="authentication required"):
+        market_data.get_quote("AAPL")
+    with pytest.raises(KisAuthError, match="authentication required"):
+        market_data.get_last_price("AAPL")
+
+    auth._store_token("fake-token", 60)
     with pytest.raises(NotImplementedError, match="official documentation"):
         market_data.get_quote("AAPL")
     with pytest.raises(NotImplementedError, match="official documentation"):
@@ -29,7 +35,7 @@ def test_market_data_methods_fail_closed(settings):
 
 
 def test_market_data_healthcheck_disconnected(settings):
-    market_data = _market_data(settings)
+    market_data, _auth = _market_data(settings)
     result = market_data.healthcheck_market_data()
     assert result["connected"] is False
     assert result["auth_required"] is True
@@ -38,7 +44,7 @@ def test_market_data_healthcheck_disconnected(settings):
 
 
 def test_market_data_repr_does_not_expose_secrets(settings):
-    market_data = _market_data(settings)
+    market_data, _auth = _market_data(settings)
     text = repr(market_data)
     assert "fake-key" not in text
     assert "fake-secret" not in text
diff --git a/projects/paper-trading/tests/test_kis_order_preflight.py b/projects/paper-trading/tests/test_kis_order_preflight.py
index d5296a6..84736e5 100644
--- a/projects/paper-trading/tests/test_kis_order_preflight.py
+++ b/projects/paper-trading/tests/test_kis_order_preflight.py
@@ -136,5 +136,12 @@ def test_place_order_runs_preflight_before_notimplemented(settings):
 
 def test_place_order_valid_input_reaches_notimplemented(settings):
     broker = KisBroker(_settings(settings))
+    ack = broker.place_order(_broker_order())
+    assert ack.status == "dry_run"
+    assert broker.last_order_preview is not None
+
+
+def test_place_order_valid_input_with_dry_run_disabled_reaches_notimplemented(settings):
+    broker = KisBroker(replace(_settings(settings), kis_order_dry_run=False))
     with pytest.raises(NotImplementedError, match="Pre-flight passed"):
         broker.place_order(_broker_order())

```

## 2026-05-15T06:19:07.464Z — claude-review

```
(no output)
```

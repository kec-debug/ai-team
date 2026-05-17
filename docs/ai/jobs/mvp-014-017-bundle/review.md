Verdict: REQUEST CHANGES

## Findings

### Medium: 공식값 갭 문서에 payload/header 예시가 남아 있음

- [docs/kis/MISSING_OFFICIAL_VALUES.md:20](/root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md:20)
- [docs/kis/MISSING_OFFICIAL_VALUES.md:21](/root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md:21)

리뷰 기준 1번은 "No KIS endpoint, TR ID, URL, header, or payload was invented"입니다. 현재 문서는 실제 값 컬럼을 `<TBD>`로 둔 점은 좋지만, 설명 칸에 `content-type`, `grant_type`, `appkey`, `appsecret` 같은 header/body 필드 예시가 들어 있습니다. 이 값들이 일반적인 OAuth 용어라 하더라도, 본 작업의 승인 범위는 KIS 공식 문서값이 없으면 header/payload 형식도 적지 않는 쪽입니다.

권장 수정:

- `Required request headers` 설명에서 구체 header 이름을 제거하고 "공식 문서 기준 필수 headers" 정도로만 남긴다.
- `Request body fields` 설명에서 `grant_type`, `appkey`, `appsecret` 예시를 제거하고 "공식 문서 기준 body fields" 정도로만 남긴다.
- 필요하면 `test_missing_official_values_doc.py`에 이 문자열들이 문서에 나타나지 않는다는 assertion을 추가한다.

### Low: 현재 worktree diff에는 mvp-014 범위 밖 변경이 함께 남아 있음

- [projects/paper-trading/app/broker/kis.py](/root/ai-dev-center/projects/ai-team/projects/paper-trading/app/broker/kis.py:68)
- [projects/paper-trading/app/config.py](/root/ai-dev-center/projects/ai-team/projects/paper-trading/app/config.py:37)
- [projects/paper-trading/.env.example](/root/ai-dev-center/projects/ai-team/projects/paper-trading/.env.example:20)

`patch.md`는 해당 변경들이 mvp-011-013의 선행 dirty worktree라고 설명합니다. 그 설명은 현재 구현 요약과 일관되지만, mvp-014-017-bundle 단독 diff로는 `app/broker/kis.py`, `app/config.py`, `.env.example`, 여러 KIS 테스트 변경이 함께 보입니다. 최종 제출/리뷰 단위에서 이 job만 검토해야 한다면 diff isolation이 약합니다. 되돌리라는 뜻은 아니며, mvp-014 리뷰에서는 선행 변경으로 명시적으로 분리되어야 합니다.

## Positive Checks

- 실제 KIS endpoint, host URL, TR ID는 추가되지 않았습니다.
- `KisHttpClient.request()`는 여전히 `NotImplementedError`이고, 확인된 공식값 없이 실제 HTTP 호출을 수행하지 않습니다.
- KIS OAuth/account/market/order HTTP 연결은 공식값 부족으로 보류되어 있습니다.
- `KIS_ORDER_DRY_RUN=true` 기본값은 유지됩니다.
- `KisBroker.place_order()` dry-run 경로는 `OrderAck(status="dry_run")`을 반환하며 HTTP client를 호출하지 않습니다.
- dry-run이 꺼진 경우도 주문 endpoint 공식값 부족으로 `NotImplementedError` fail-closed입니다.
- live trading 차단과 market order 차단은 유지됩니다.
- `/paper/status`는 `kis_order_dry_run`을 bool로만 노출하며 app key, app secret, 원문 계좌번호, token을 노출하지 않습니다.
- Strategy/Agent/LLM에서 KIS 직접 호출 경로는 확인되지 않았습니다. `app/agents` 디렉터리는 현재 존재하지 않습니다.
- OMS/RiskEngine 경계를 우회하는 변경은 확인되지 않았습니다.
- `.env`는 git status에 나타나지 않았습니다.

## Tests / Verification

Codex patch report 기준:

- `.venv/bin/python -m compileall app tests` passed
- `.venv/bin/python -m pytest -p no:cacheprovider -q tests/test_missing_official_values_doc.py` → 3 passed
- `.venv/bin/python -m pytest -p no:cacheprovider` → 129 passed in 0.25s

리뷰 단계에서는 사용자의 "Do not run arbitrary shell commands" 지시에 맞춰 테스트를 재실행하지 않고, job 문서와 지정 diff 중심으로 확인했습니다.

## Final Checklist

- No KIS endpoint/TR ID/URL invented: PASS
- No header/payload invented: REQUEST CHANGES, 문서 예시 제거 필요
- Official values missing → fail-closed: PASS
- `KIS_ORDER_DRY_RUN=true` default: PASS
- Dry-run does not send HTTP orders: PASS
- Live trading remains disabled: PASS
- Market orders remain disabled: PASS
- No real KIS key/secret/account/token exposed: PASS
- `.env` not added to git: PASS
- Strategy/Agent/LLM cannot call KIS directly: PASS
- OMS/RiskEngine boundary intact: PASS
- `/paper/status` does not expose secrets: PASS
- Tests passed: REPORTED PASS, not rerun during review
- Scope stayed within mvp-014-017-bundle: PARTIAL, intended mvp-014 changes are scoped but current worktree includes pre-existing out-of-scope diffs

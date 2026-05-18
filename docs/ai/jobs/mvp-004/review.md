# Review — mvp-004: AI 개발팀 GUI 화면 배치 개선

## Verdict

**APPROVE**

mvp-004 구현이 계획서(`plan.md`)와 사용자 요청(`request.ko.md`)을 정확히 반영했다. DOM 순서, 작업 설정 details 분리, textarea 축소, 그리드 → 단일 컬럼 전환, 안전 가드 모두 충족. 검증 명령(`node --check`)도 통과. commit 단계에서 사람이 staging 범위만 한정하면 된다.

## 검증된 사실

1. **DOM 순서가 요청과 일치한다.** (`web/public/index.html`)
   - line 19 `quick-actions` → line 40 `control-panel` → line 57 `tmux-panel` → line 65 `pipeline-status` → line 109 `job-settings`(details) → line 128 `advanced-panel`(details) → line 139 `artifacts` → line 147 `result-summary` → line 169 `output-panel`.
   - 요청 4번의 우선순위(상단: 핵심 실행 → 승인/서비스 제어/실시간 출력 → 파이프라인 상태 → 작업 설정/고급/산출물/출력)와 정합.
2. **`<section class="panel setup">`이 HTML에서 완전히 사라졌다.** `grep "panel setup" web/public/index.html web/public/style.css` 결과 0건.
3. **textarea가 `rows="6"`으로 축소되었다.** `web/public/index.html:27 <textarea id="inputKo" spellcheck="false" rows="6">`.
4. **CSS 단일 컬럼 전환.** `web/public/style.css` line 64–73: `.layout { display: flex; flex-direction: column; gap:18px; padding:22px; max-width:1100px; margin: 0 auto; }`. `.setup { grid-row: span 4; }`, `.output-panel { grid-column: 2; }` 제거됨.
5. **textarea `min-height` 축소.** `style.css`의 textarea 규칙이 `min-height: 140px`로 변경 (기존 330px).
6. **신규 클래스 스타일 추가.** `.quick-actions { display: grid; gap: 12px; }`, `.job-settings { padding: 14px 18px; }`, `.job-settings > summary { cursor: pointer; ... }`, `.job-settings[open] { padding-bottom: 18px; }` 모두 존재.
7. **반응형 미디어 쿼리 정리.** `@media (max-width: 920px) { .layout { padding: 14px; } ... }`로 단순화. 단일 컬럼이 기본이라 `grid-template-columns: 1fr` 분기와 `.setup, .output-panel { grid-row: auto; grid-column: auto; }` 분기 제거됨. `.step-grid`, `.role-display`, `.pipeline-meta`, `.primary-actions` 1-column 분기는 보존.
8. **기존 ID와 `data-send` 보존.** `grep -cE 'id="(projectDir|jobId|inputKo|runPipeline|tmuxWindow|tmuxOutput|approveOnce|approveSession|rejectAction|interruptAction|refreshTmuxOutput|refreshStatus|pipelineStatus|resetPipeline|startTeam|createJob|saveInput|gitStatus|gitDiff|loadArtifacts|clearOutput|approvalModal)"' = 22 (요청한 22개 모두 존재). `data-send="claude-plan|codex-implement|claude-review"` 매칭 3건.
9. **`web/public/app.js`와 `web/server.js`는 무변경.** `git diff --stat -- web/public/app.js web/server.js` 빈 결과.
10. **`projects/paper-trading/` 미존재 = 미변경.** mvp-003 영역에 손대지 않음.
11. **옛 5-역할 라벨 재노출 없음.** `grep -nE "Gemini Manager|Claude Architect|Claude Reviewer|Git Shell" web/public/index.html web/public/style.css` 0건.
12. **`node --check` 둘 다 통과.** `web/server.js OK`, `web/public/app.js OK`.
13. **수동 유틸리티 보존.** `git status`(`#gitStatus`), `git diff`(`#gitDiff`)는 `advanced-panel` details 내부에 그대로 유지. commit/push/merge 자동화 버튼 신설 없음.
14. **임의 shell 입력 신설 없음.** 새 endpoint나 새 fetch 호출 없음 (`app.js`, `server.js` 무변경).

## Findings (severity 순)

### 1. (low / process) `git diff --stat`에 `docs/ai/jobs/mvp-004/request.ko.md`가 포함됨

- 위치: `local-diff.patch` line 1–87, `patch.md` line 39–44 / line 81–86.
- 관찰: 본 작업은 UI 레이아웃 한정인데도 `request.ko.md`가 +78 라인 diff로 잡혔다. 원인은 Codex의 변경이 아니라 파이프라인의 `save-input` 단계가 이미 committed 상태였던 옛 `request.ko.md`(이전 사용자 요청 — "GUI 파이프라인이 Claude 계획 완료 전에 Codex 단계로 넘어가는 문제…")를 현재 mvp-004 요청(GUI 화면 배치 개선)으로 덮어쓴 결과다. 새 내용은 사용자가 이번 세션에서 보낸 요청과 일치한다.
- 영향: 안전 측면 문제 없음. 단 사람이 `git add -A`로 staging 하면 의도와 다른 변경이 함께 들어갈 수 있고, 또한 추후 같은 mvp-004 job ID로 파이프라인을 재실행하면 같은 충돌이 재발할 수 있다.
- 권장: commit 시 `git add -- web/public/index.html web/public/style.css docs/ai/jobs/mvp-004/`(또는 mvp-004의 산출물만)로 staging을 한정한다. mvp-003 산출물(`docs/ai/jobs/mvp-003/...`)은 별도 commit으로 분리한다.
- 참고: 새 `request.ko.md` 마지막 줄에 newline이 빠져 `\ No newline at end of file` 경고가 있다. 매우 작은 흠집이며 본 작업 범위 밖.

### 2. (informational) `web/public/app.js`를 손대지 않은 것이 의도적이다

- 관찰: `app.js`는 모든 셀렉터가 ID 기반이고 HTML 재배열에 영향을 받지 않으므로 변경 불필요. Codex가 이를 정확히 인식하고 손대지 않았다.
- 영향: 좋음. 행동 변경 위험 없음.

### 3. (informational) `web/server.js`와 README/Workflow 문서를 손대지 않은 것이 의도적이다

- README와 `docs/ai/CLAUDE_CODEX_WORKFLOW.md`에 "왼쪽/오른쪽 컬럼" 같은 시각 배치 표현이 없어 doc 보정 불필요. Codex가 plan §4.6 가이드라인을 따라 손대지 않았다.

## File / line references (요청 ↔ 산출물 매핑)

| 요청 항목 | 산출물 위치 | 상태 |
| --- | --- | --- |
| 1. 파이프라인 상태를 전체 실행 버튼 아래로 | `index.html` line 19(quick-actions) ≪ line 65(pipeline-status) | ✓ |
| 2. 승인/거절/중단/서비스 제어/실시간 출력을 상단 쪽으로 | `control-panel` line 40, `tmux-panel` line 57 | ✓ |
| 3. 작업 설정을 짧고 컴팩트하게 + 접기/펼치기 + 입력칸 높이 축소 | `details.job-settings` line 109, textarea `rows="6"`, CSS `min-height: 140px` | ✓ |
| 4. 우선순위 재배치 (상단→하단) | DOM 순서 일치 | ✓ |
| 5. Claude+Codex 2-role 유지, 옛 5-역할 미노출, 4개 메인 버튼 유지 | `data-send` 3종, runPipeline 버튼, 옛 라벨 0건 | ✓ |
| 6. git status/git diff 수동 유틸리티만, commit/push/merge 자동화 금지 | `advanced-panel` details의 `#gitStatus`, `#gitDiff`. 자동화 버튼/엔드포인트 신설 없음 | ✓ |
| 7. 반응형 유지 | `.layout` flex column 단일 컬럼 + `@media (max-width: 920px)` 패딩 조정 + 1-column 분기 보존 | ✓ |

## Missing tests / residual risk

- 사람이 직접 브라우저로 화면을 보면서 (a) 작은 화면(예: 480px)에서 `pre#tmuxOutput`과 `.control-actions`가 잘리지 않는지, (b) 승인 모달이 가려지지 않는지, (c) `<details>` 접기/펼치기가 부드럽게 작동하는지를 한 번 확인하는 것이 좋다. 코드 측 자동 테스트는 본 작업 범위에 없다.
- `docs/ai/jobs/mvp-003/`(BLOCK 상태)은 그대로 untracked로 남아 있다. mvp-004 commit과 섞이지 않도록 staging 시 주의.

## Final checklist (approved scope + safety rules)

- [x] DOM 순서가 요청 우선순위와 일치한다.
- [x] `핵심 실행` 패널이 최상단이며 `작업 ID`, `한국어 작업 요청`, 4개 메인 버튼만 포함한다.
- [x] `승인 / 서비스 제어`, `실시간 tmux 출력`이 그 바로 아래에 노출된다.
- [x] `파이프라인 상태`가 그 아래로 이동했다.
- [x] `작업 설정`이 `<details class="panel job-settings">`로 분리되었고 기본 닫힘이다.
- [x] textarea가 `rows="6"`으로 축소되었고 CSS `min-height`도 축소(140px)되었다.
- [x] `.setup`, `.output-panel` 그리드 규칙이 CSS에서 제거되었다.
- [x] `.layout`이 단일 컬럼 flex로 단순화되었다.
- [x] 모든 기존 ID와 `data-send`/`data-approval-action` 속성이 보존되어 JS 핸들러가 깨지지 않는다.
- [x] 옛 5-역할이 메인 UI에 재노출되지 않는다.
- [x] `git status`, `git diff`만 수동 유틸리티 버튼으로 남아 있다. `commit`/`push`/`merge` 자동화 신설 없음.
- [x] 임의 shell 입력 UI/API 신설 없음.
- [x] `projects/paper-trading/`, `.env`, secrets, auth, payment, migration, infra 미변경.
- [x] `node --check web/server.js`, `node --check web/public/app.js`가 모두 통과한다.
- [x] `patch.md`에 (i) 옮긴 영역, (ii) 작업 설정 축소 방법, (iii) Claude+Codex 구조 유지, (iv) 테스트 결과가 모두 들어 있다.
- [ ] **`git diff --stat`에 mvp-004 외 변경 없음 — 부분 충족.** UI 두 파일은 OK. `docs/ai/jobs/mvp-004/request.ko.md`가 함께 변경되었지만, 이는 Codex가 아닌 파이프라인 `save-input`의 산출물이며 사용자 요청과 일치하는 내용이다. 사람이 commit 시 staging만 한정하면 문제 없음(Findings #1).

## 사람에게 남기는 액션 아이템

1. commit 시 다음으로 staging을 한정한다.
   - `web/public/index.html`
   - `web/public/style.css`
   - `docs/ai/jobs/mvp-004/` 산출물(`request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`, 필요 시 `local-diff.patch`, `pipeline.log.md`)
2. **mvp-003 산출물은 별도 커밋으로 분리한다.** mvp-003은 BLOCK 상태이므로 같은 commit에 묶지 말 것. 또한 mvp-003의 구현이 미완이므로 코드 변경(`projects/paper-trading/`)이 없는 채로 산출물만 커밋되는 점을 인지하고, 차후 mvp-003 재실행 결과와 함께 정리할지 결정한다.
3. `git diff --cached --stat`으로 staging 범위를 한 번 더 확인한다.
4. (선택, 권장) 브라우저로 새 레이아웃을 한 번 열어 (a) 480px 화면에서 모든 패널이 보이는지, (b) `<details class="panel job-settings">` 토글이 동작하는지, (c) 승인 모달이 가려지지 않는지를 직접 확인한다.
5. PR 머지·푸시·배포는 사람이 직접 결정한다. 본 작업은 자동화하지 않는다.

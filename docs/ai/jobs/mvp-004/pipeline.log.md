
## 2026-05-14T08:36:47.819Z — create-job

```
Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-004
```

## 2026-05-14T08:36:47.819Z — save-input

```
Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-004/request.ko.md
```

## 2026-05-14T08:36:47.828Z — claude-plan

```
(no output)
```

## 2026-05-14T08:39:32.861Z — codex-implement

```
(no output)
```

## 2026-05-14T08:44:42.909Z — save-diff

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
diff --git a/web/public/index.html b/web/public/index.html
index a02de7a..3f48d96 100644
--- a/web/public/index.html
+++ b/web/public/index.html
@@ -16,32 +16,17 @@
     </header>
 
     <main class="layout">
-      <section class="panel setup">
-        <h2>작업 설정</h2>
-        <label>
-          프로젝트 경로
-          <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
-        </label>
+      <section class="panel quick-actions">
+        <h2>핵심 실행</h2>
         <label>
           작업 ID
           <input id="jobId" type="text" value="mvp-001" autocomplete="off" spellcheck="false">
         </label>
         <label>
           한국어 작업 요청
-          <textarea id="inputKo" spellcheck="false" rows="14"></textarea>
+          <textarea id="inputKo" spellcheck="false" rows="6"></textarea>
         </label>
         <p class="field-hint">여기에는 한국어 작업 요청만 입력하세요. 쉘 설정 명령, 실행 명령, 토큰, 비밀값은 넣지 않습니다.</p>
-        <div class="role-display" aria-label="역할 안내">
-          <div>
-            <strong>Claude</strong>
-            <span>planning / requirements / review</span>
-          </div>
-          <div>
-            <strong>Codex</strong>
-            <span>implementation / tests / patch summary</span>
-          </div>
-        </div>
-        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
         <div class="pipeline-runner">
           <button id="runPipeline" class="primary-action" type="button">Claude → Codex → Claude 전체 실행</button>
           <div class="primary-actions">
@@ -52,6 +37,31 @@
         </div>
       </section>
 
+      <section class="panel control-panel">
+        <h2>승인 / 서비스 제어</h2>
+        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
+        <label>
+          제어할 tmux 창
+          <select id="tmuxWindow"></select>
+        </label>
+        <div class="actions control-actions">
+          <button id="approveOnce" type="button">승인 / 계속 진행</button>
+          <button id="approveSession" type="button">세션 승인</button>
+          <button id="rejectAction" type="button">거절</button>
+          <button id="interruptAction" type="button">중단</button>
+          <button id="restartAiTeam" type="button">AI팀 재시작</button>
+          <button id="restartGui" type="button">GUI 서버 재시작</button>
+        </div>
+      </section>
+
+      <section class="panel tmux-panel">
+        <div class="panel-head">
+          <h2>실시간 tmux 출력</h2>
+          <button id="refreshTmuxOutput" type="button">출력 새로고침</button>
+        </div>
+        <pre id="tmuxOutput" aria-live="polite"></pre>
+      </section>
+
       <section class="panel pipeline-status">
         <div class="panel-head">
           <h2>파이프라인 상태</h2>
@@ -96,29 +106,42 @@
         <div id="pipelineSteps" class="pipeline-steps"></div>
       </section>
 
-      <section class="panel control-panel">
-        <h2>승인 / 서비스 제어</h2>
-        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
+      <details class="panel job-settings">
+        <summary>작업 설정</summary>
         <label>
-          제어할 tmux 창
-          <select id="tmuxWindow"></select>
+          프로젝트 경로
+          <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
         </label>
-        <div class="actions control-actions">
-          <button id="approveOnce" type="button">승인 / 계속 진행</button>
-          <button id="approveSession" type="button">세션 승인</button>
-          <button id="rejectAction" type="button">거절</button>
-          <button id="interruptAction" type="button">중단</button>
-          <button id="restartAiTeam" type="button">AI팀 재시작</button>
-          <button id="restartGui" type="button">GUI 서버 재시작</button>
+        <div class="role-display" aria-label="역할 안내">
+          <div>
+            <strong>Claude</strong>
+            <span>planning / requirements / review</span>
+          </div>
+          <div>
+            <strong>Codex</strong>
+            <span>implementation / tests / patch summary</span>
+          </div>
         </div>
-      </section>
+        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
+      </details>
 
-      <section class="panel tmux-panel">
+      <details class="panel advanced-panel">
+        <summary>고급 제어</summary>
+        <div class="actions">
+          <button id="startTeam" type="button">AI 팀 시작</button>
+          <button id="createJob" type="button">작업 폴더 생성</button>
+          <button id="saveInput" type="button">request.ko.md 저장</button>
+          <button id="gitStatus" type="button">git status</button>
+          <button id="gitDiff" type="button">git diff</button>
+        </div>
+      </details>
+
+      <section class="panel artifacts">
         <div class="panel-head">
-          <h2>실시간 tmux 출력</h2>
-          <button id="refreshTmuxOutput" type="button">출력 새로고침</button>
+          <h2>산출물</h2>
+          <button id="loadArtifacts" type="button">목록 새로고침</button>
         </div>
-        <pre id="tmuxOutput" aria-live="polite"></pre>
+        <div id="artifactList" class="artifact-list"></div>
       </section>
 
       <section class="panel result-summary">
@@ -143,25 +166,6 @@
         </dl>
       </section>
 
-      <details class="panel advanced-panel">
-        <summary>고급 제어</summary>
-        <div class="actions">
-          <button id="startTeam" type="button">AI 팀 시작</button>
-          <button id="createJob" type="button">작업 폴더 생성</button>
-          <button id="saveInput" type="button">request.ko.md 저장</button>
-          <button id="gitStatus" type="button">git status</button>
-          <button id="gitDiff" type="button">git diff</button>
-        </div>
-      </details>
-
-      <section class="panel artifacts">
-        <div class="panel-head">
-          <h2>산출물</h2>
-          <button id="loadArtifacts" type="button">목록 새로고침</button>
-        </div>
-        <div id="artifactList" class="artifact-list"></div>
-      </section>
-
       <section class="panel output-panel">
         <div class="panel-head">
           <h2>출력</h2>
diff --git a/web/public/style.css b/web/public/style.css
index 9d50479..0158ea3 100644
--- a/web/public/style.css
+++ b/web/public/style.css
@@ -64,11 +64,11 @@ h2 {
 }
 
 .layout {
-  display: grid;
-  grid-template-columns: minmax(320px, 0.95fr) minmax(360px, 1.05fr);
+  display: flex;
+  flex-direction: column;
   gap: 18px;
   padding: 22px;
-  max-width: 1440px;
+  max-width: 1100px;
   margin: 0 auto;
 }
 
@@ -80,14 +80,6 @@ h2 {
   padding: 18px;
 }
 
-.setup {
-  grid-row: span 4;
-}
-
-.output-panel {
-  grid-column: 2;
-}
-
 .panel-head {
   display: flex;
   align-items: center;
@@ -103,6 +95,26 @@ h2 {
   justify-content: flex-end;
 }
 
+.quick-actions {
+  display: grid;
+  gap: 12px;
+}
+
+.job-settings {
+  padding: 14px 18px;
+}
+
+.job-settings > summary {
+  cursor: pointer;
+  font-size: 18px;
+  font-weight: 800;
+  padding: 4px 0;
+}
+
+.job-settings[open] {
+  padding-bottom: 18px;
+}
+
 label {
   display: grid;
   gap: 7px;
@@ -173,7 +185,7 @@ select {
 }
 
 textarea {
-  min-height: 330px;
+  min-height: 140px;
   resize: vertical;
   padding: 12px;
   line-height: 1.5;
@@ -610,16 +622,9 @@ pre {
   }
 
   .layout {
-    grid-template-columns: 1fr;
     padding: 14px;
   }
 
-  .setup,
-  .output-panel {
-    grid-row: auto;
-    grid-column: auto;
-  }
-
   .step-grid {
     grid-template-columns: 1fr;
   }

```

## 2026-05-14T08:44:42.915Z — claude-review

```
(no output)
```

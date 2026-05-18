const state = {
  projectDir: localStorage.getItem('aiTeamProjectDir') || '',
  jobId: localStorage.getItem('aiTeamJobId') || 'mvp-001'
};

const projectDirEl = document.querySelector('#projectDir');
const jobIdEl = document.querySelector('#jobId');
const inputKoEl = document.querySelector('#inputKo');
const outputEl = document.querySelector('#output');
const artifactListEl = document.querySelector('#artifactList');
const runPipelineButton = document.querySelector('#runPipeline');
const sendButtons = [...document.querySelectorAll('[data-send]')];
const pipelineStateEl = document.querySelector('#pipelineState');
const pipelineJobIdEl = document.querySelector('#pipelineJobId');
const pipelineStageEl = document.querySelector('#pipelineStage');
const pipelineStateNameEl = document.querySelector('#pipelineStateName');
const pipelineUpdatedAtEl = document.querySelector('#pipelineUpdatedAt');
const pipelineTargetWindowEl = document.querySelector('#pipelineTargetWindow');
const pipelineWaitingApprovalEl = document.querySelector('#pipelineWaitingApproval');
const detectedIssueAlertEl = document.querySelector('#detectedIssueAlert');
const pipelineGuidanceEl = document.querySelector('#pipelineGuidance');
const approvalInlinePromptEl = document.querySelector('#approvalInlinePrompt');
const reopenApprovalPopupEl = document.querySelector('#reopenApprovalPopup');
const pipelineStepsEl = document.querySelector('#pipelineSteps');
const summaryArtifactsEl = document.querySelector('#summaryArtifacts');
const summaryDiffEl = document.querySelector('#summaryDiff');
const summaryReviewEl = document.querySelector('#summaryReview');
const summaryNextActionEl = document.querySelector('#summaryNextAction');
const tmuxWindowEl = document.querySelector('#tmuxWindow');
const tmuxOutputEl = document.querySelector('#tmuxOutput');
const approvalModalEl = document.querySelector('#approvalModal');
const approvalModalStepEl = document.querySelector('#approvalModalStep');
const approvalModalWindowEl = document.querySelector('#approvalModalWindow');
const approvalModalSummaryEl = document.querySelector('#approvalModalSummary');
const approvalModalTypeEl = document.querySelector('#approvalModalType');
const approvalModalCommandEl = document.querySelector('#approvalModalCommand');
const approvalModalCwdEl = document.querySelector('#approvalModalCwd');
const approvalModalRiskEl = document.querySelector('#approvalModalRisk');
const approvalModalRecommendationEl = document.querySelector('#approvalModalRecommendation');
const approvalModalRawEl = document.querySelector('#approvalModalRaw');
const approvalModalRiskWarningEl = document.querySelector('#approvalModalRiskWarning');
const approvalModalApproveOnceEl = document.querySelector('#approvalModalApproveOnce');
const approvalModalApproveSessionEl = document.querySelector('#approvalModalApproveSession');
const aiControlButtons = [
  document.querySelector('#approveOnce'),
  document.querySelector('#approveSession'),
  document.querySelector('#rejectAction'),
  document.querySelector('#interruptAction')
];
let pipelinePollTimer = null;
let liveRefreshTimer = null;
let lastApprovalKey = null;
let currentApprovalRequest = null;
const manualRequiredMessage = 'AI CLI 창에서 승인 대기 중일 수 있습니다. 아래 승인 버튼을 누르거나 tmux 출력을 확인하세요.';
const detectedIssueMessages = {
  blocked: 'AI가 작업을 차단했습니다. 작업 범위를 줄이거나 금지 항목을 별도 작업으로 분리한 뒤 다시 실행하세요.',
  approval_required: 'AI CLI가 승인 대기 중일 수 있습니다. 승인/세션 승인/거절/중단 버튼을 사용하세요.',
  failed: '실행 오류가 감지되었습니다. 로그를 확인하고 인증/명령/서버 상태를 점검하세요.',
  manual_review_required: manualRequiredMessage
};
const activePipelineStates = new Set([
  'claude_planning',
  'codex_implementing',
  'claude_reviewing',
  'approval_required'
]);
const finalPipelineStates = new Set([
  'succeeded',
  'failed',
  'blocked',
  'manual_review_required',
  'review_approved',
  'review_changes_requested',
  'manual_final_approval_required',
  'idle'
]);
const stageWindows = {
  'claude-plan': 'claude',
  'codex-implement': 'codex',
  'claude-review': 'claude',
  'codex-review-fix': 'codex',
  'claude-re-review': 'claude'
};

projectDirEl.value = state.projectDir;
jobIdEl.value = state.jobId;

const defaultInput = `# 작업 요청

한국어 작업 요청을 여기에 작성하세요.

## 목표

- 무엇을 만들거나 고칠지 적습니다.
- 완료 기준을 구체적으로 적습니다.
`;

loadInputForCurrentJob();

function inputStorageKey(projectDir, jobId) {
  return `aiTeamInputKo:${projectDir || '-'}:${jobId || '-'}`;
}

function loadInputForCurrentJob() {
  const projectDir = projectDirEl.value.trim();
  const jobId = jobIdEl.value.trim();
  inputKoEl.value = localStorage.getItem(inputStorageKey(projectDir, jobId)) || defaultInput;
}

function getForm() {
  const projectDir = projectDirEl.value.trim();
  const jobId = jobIdEl.value.trim();
  const inputKo = inputKoEl.value;
  localStorage.setItem('aiTeamProjectDir', projectDir);
  localStorage.setItem('aiTeamJobId', jobId);
  localStorage.setItem(inputStorageKey(projectDir, jobId), inputKo);
  return { projectDir, jobId, inputKo };
}

function writeOutput(title, payload) {
  const time = new Date().toLocaleTimeString('ko-KR', { hour12: false });
  const body = typeof payload === 'string'
    ? payload
    : payload.output || payload.content || payload.error || JSON.stringify(payload, null, 2);
  outputEl.textContent = `[${time}] ${title}\n${body || '(출력 없음)'}\n\n${outputEl.textContent}`;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const text = await response.text();
    const preview = text.trim().slice(0, 160) || '(빈 응답)';
    throw new Error(`서버가 JSON이 아닌 응답을 반환했습니다. API 서버 경로와 실행 중인 서버를 확인하세요. 응답 미리보기: ${preview}`);
  }

  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || data.message || '요청 실패');
  }
  return data;
}

async function runAction(title, callback) {
  try {
    const result = await callback();
    writeOutput(title, result);
    return result;
  } catch (error) {
    writeOutput(`${title} 실패`, error.message);
    return null;
  }
}

document.querySelector('#refreshStatus').addEventListener('click', () => {
  runAction('AI 팀 상태', () => requestJson('/api/status'));
});

projectDirEl.addEventListener('change', () => {
  localStorage.setItem('aiTeamProjectDir', projectDirEl.value.trim());
  loadInputForCurrentJob();
  refreshPipelineStatus();
});

jobIdEl.addEventListener('change', () => {
  localStorage.setItem('aiTeamJobId', jobIdEl.value.trim());
  loadInputForCurrentJob();
  refreshPipelineStatus();
});

document.querySelector('#startTeam').addEventListener('click', () => {
  runAction('AI 팀 시작', () => requestJson('/api/start', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
});

document.querySelector('#createJob').addEventListener('click', () => {
  runAction('작업 폴더 생성', () => requestJson('/api/create-job', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
});

document.querySelector('#saveInput').addEventListener('click', () => {
  runAction('request.ko.md 저장', () => requestJson('/api/save-input', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
});

runPipelineButton.addEventListener('click', async () => {
  const result = await runAction('Claude → Codex → Claude 전체 실행', () => requestJson('/api/pipeline/run', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
  if (result) {
    startPipelinePolling();
  }
});

document.querySelector('#pipelineStatus').addEventListener('click', refreshPipelineStatus);
document.querySelector('#finalManualReview').addEventListener('click', () => {
  writeOutput('최종 확인', 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.');
  refreshPipelineStatus();
});

document.querySelector('#resetPipeline').addEventListener('click', async () => {
  const result = await runAction('파이프라인 상태 초기화', () => requestJson('/api/pipeline/reset', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
  if (result) {
    if (pipelinePollTimer) {
      clearInterval(pipelinePollTimer);
      pipelinePollTimer = null;
    }
    refreshPipelineStatus();
  }
});

document.querySelector('#approveOnce').addEventListener('click', () => sendTmuxControl('승인 / 계속 진행', '/api/tmux/approve-once'));
document.querySelector('#approveSession').addEventListener('click', () => sendTmuxControl('세션 승인', '/api/tmux/approve-session'));
document.querySelector('#rejectAction').addEventListener('click', () => sendTmuxControl('거절', '/api/tmux/reject'));
document.querySelector('#interruptAction').addEventListener('click', () => sendTmuxControl('중단', '/api/tmux/interrupt'));
document.querySelector('#closeApprovalModal').addEventListener('click', closeApprovalModal);
document.querySelector('#dismissApprovalModal').addEventListener('click', closeApprovalModal);
reopenApprovalPopupEl.addEventListener('click', () => {
  if (currentApprovalRequest) {
    openApprovalModal(currentApprovalRequest, true);
  }
});
document.querySelectorAll('[data-approval-action]').forEach((button) => {
  button.addEventListener('click', () => sendApprovalModalAction(button.dataset.approvalAction));
});
document.querySelector('#refreshTmuxOutput').addEventListener('click', refreshTmuxOutput);
tmuxWindowEl.addEventListener('change', refreshTmuxOutput);
tmuxWindowEl.addEventListener('change', updateTmuxControlState);

document.querySelector('#restartAiTeam').addEventListener('click', () => {
  runAction('AI팀 재시작', () => requestJson('/api/service/restart-ai-team', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
});

document.querySelector('#restartGui').addEventListener('click', () => {
  restartGuiServer();
});

async function restartGuiServer() {
  const result = await runAction('GUI 서버 재시작', () => requestJson('/api/service/restart-gui', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
  if (!result) {
    return;
  }

  writeOutput('GUI 서버 재시작 요청 완료', '3~5초 뒤 자동 확인합니다');
  setTimeout(checkGuiRestartStatus, 5000);
}

async function checkGuiRestartStatus() {
  try {
    const result = await requestJson('/api/status');
    writeOutput('GUI 서버 재시작 확인', result.output || 'GUI 서버가 다시 응답합니다.');
  } catch (error) {
    writeOutput(
      'GUI 서버 재시작 확인 실패',
      '아직 서버가 올라오지 않았습니다. 잠시 후 새로고침하거나 수동 복구 명령을 실행하세요.'
    );
  }
}

document.querySelectorAll('[data-send]').forEach((button) => {
  button.addEventListener('click', () => {
    const target = button.dataset.send;
    runAction(`${button.textContent}`, () => requestJson(`/api/send/${target}`, {
      method: 'POST',
      body: JSON.stringify(getForm())
    }));
  });
});

document.querySelector('#gitStatus').addEventListener('click', () => {
  const { projectDir } = getForm();
  runAction('git status', () => requestJson(`/api/git/status?projectDir=${encodeURIComponent(projectDir)}`));
});

document.querySelector('#gitDiff').addEventListener('click', () => {
  const { projectDir } = getForm();
  runAction('git diff', () => requestJson(`/api/git/diff?projectDir=${encodeURIComponent(projectDir)}`));
});

document.querySelector('#loadArtifacts').addEventListener('click', loadArtifacts);

document.querySelector('#clearOutput').addEventListener('click', () => {
  outputEl.textContent = '';
});

async function loadArtifacts() {
  const { projectDir, jobId } = getForm();
  const result = await runAction('산출물 목록', () => requestJson(
    `/api/artifacts?projectDir=${encodeURIComponent(projectDir)}&jobId=${encodeURIComponent(jobId)}`
  ));
  artifactListEl.textContent = '';
  if (!result || !result.files || result.files.length === 0) {
    artifactListEl.textContent = '표시할 산출물이 없습니다.';
    return;
  }

  result.files.forEach((file) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = file.name;
    button.addEventListener('click', () => openArtifact(file.path));
    artifactListEl.appendChild(button);
  });
}

function openArtifact(filePath) {
  const { projectDir } = getForm();
  runAction(`산출물: ${filePath}`, () => requestJson(
    `/api/artifact?projectDir=${encodeURIComponent(projectDir)}&path=${encodeURIComponent(filePath)}`
  ));
}

function startPipelinePolling() {
  if (pipelinePollTimer) {
    clearInterval(pipelinePollTimer);
  }
  refreshPipelineStatus();
  pipelinePollTimer = setInterval(refreshPipelineStatus, 2000);
}

function startLiveRefresh() {
  if (liveRefreshTimer) {
    clearInterval(liveRefreshTimer);
  }
  refreshLiveViews();
  liveRefreshTimer = setInterval(refreshLiveViews, 2000);
}

function refreshLiveViews() {
  refreshPipelineStatus();
  refreshTmuxOutput();
}

async function refreshPipelineStatus() {
  const { projectDir, jobId } = getForm();
  if (!projectDir || !jobId) {
    renderPipelineStatus(null);
    return null;
  }

  try {
    const status = await requestJson(
      `/api/pipeline/status?projectDir=${encodeURIComponent(projectDir)}&jobId=${encodeURIComponent(jobId)}`
    );
    renderPipelineStatus(status);
    const pipeline = normalizePipelineStatus(status);
    if (pipelinePollTimer && finalPipelineStates.has(pipeline.state)) {
      clearInterval(pipelinePollTimer);
      pipelinePollTimer = null;
      loadArtifacts();
    }
    return status;
  } catch (error) {
    writeOutput('파이프라인 상태 실패', error.message);
    return null;
  }
}

function renderPipelineStatus(status) {
  if (!status) {
    pipelineStateEl.textContent = '프로젝트 경로와 작업 ID를 입력하세요.';
    pipelineJobIdEl.textContent = '-';
    pipelineStageEl.textContent = '-';
    pipelineStateNameEl.textContent = 'idle';
    pipelineUpdatedAtEl.textContent = '-';
    pipelineTargetWindowEl.textContent = '-';
    pipelineWaitingApprovalEl.textContent = '-';
    detectedIssueAlertEl.hidden = true;
    detectedIssueAlertEl.textContent = '';
    pipelineGuidanceEl.hidden = true;
    pipelineGuidanceEl.textContent = '';
    approvalInlinePromptEl.hidden = true;
    pipelineStepsEl.textContent = '';
    summaryArtifactsEl.textContent = '-';
    summaryDiffEl.textContent = '-';
    summaryReviewEl.textContent = '-';
    runPipelineButton.disabled = false;
    updateSendButtonGates(null);
    return;
  }

  const pipeline = normalizePipelineStatus(status);
  const currentForm = getForm();
  const current = pipeline.step ? ` / 현재 단계: ${pipeline.step}` : '';
  const approvalRequest = getApprovalRequest(status, pipeline);
  pipelineStateEl.textContent = approvalRequest
    ? '승인 대기 중 — 팝업에서 처리하세요.'
    : `${pipeline.state}: ${pipeline.message}${current}`;
  pipelineStateEl.dataset.status = pipeline.state;
  runPipelineButton.disabled = activePipelineStates.has(pipeline.state);
  pipelineJobIdEl.textContent = status.jobId || currentForm.jobId || '-';
  pipelineStageEl.textContent = pipeline.step || '-';
  pipelineStateNameEl.textContent = pipeline.state;
  pipelineUpdatedAtEl.textContent = status.updatedAt ? new Date(status.updatedAt).toLocaleTimeString('ko-KR', { hour12: false }) : '-';
  pipelineTargetWindowEl.textContent = pipeline.targetWindow || '-';
  pipelineWaitingApprovalEl.textContent = pipeline.waitingApproval ? '예' : '아니오';
  renderDetectedIssue(approvalRequest ? null : pipeline.detectedIssue);
  updateSendButtonGates(pipeline);

  if (pipeline.targetWindow && tmuxWindowEl.value !== pipeline.targetWindow) {
    tmuxWindowEl.value = pipeline.targetWindow;
    refreshTmuxOutput();
  }

  if (approvalRequest) {
    pipelineGuidanceEl.hidden = true;
    pipelineGuidanceEl.textContent = '';
    approvalInlinePromptEl.hidden = false;
    currentApprovalRequest = approvalRequest;
    openApprovalModal(approvalRequest, false);
  } else if (pipeline.state === 'manual_review_required') {
    currentApprovalRequest = null;
    closeApprovalModal();
    pipelineGuidanceEl.hidden = false;
    pipelineGuidanceEl.textContent = pipeline.message || manualRequiredMessage;
    approvalInlinePromptEl.hidden = true;
  } else {
    currentApprovalRequest = null;
    closeApprovalModal();
    const requirementsText = renderRequirementsText(pipeline.requirements);
    pipelineGuidanceEl.hidden = !requirementsText;
    pipelineGuidanceEl.textContent = requirementsText;
    approvalInlinePromptEl.hidden = true;
  }

  pipelineStepsEl.textContent = '';
  if (!status.steps || status.steps.length === 0) {
    pipelineStepsEl.textContent = '표시할 단계가 없습니다.';
  } else {
    status.steps.forEach((step) => {
      const item = document.createElement('div');
      item.className = 'pipeline-step';
      item.dataset.status = step.status;

      const label = document.createElement('strong');
      label.textContent = step.label;

      const badge = document.createElement('span');
      badge.textContent = step.status;

      const detail = document.createElement('small');
      detail.textContent = step.detail || '';

      item.append(label, badge, detail);
      pipelineStepsEl.appendChild(item);
    });
  }

  const summary = status.summary || {};
  const artifacts = summary.createdArtifacts || pipeline.artifacts.map((artifact) => artifact.name || artifact);
  summaryArtifactsEl.textContent = artifacts.length > 0 ? artifacts.join(', ') : '-';

  const gitDiff = summary.gitDiff || {};
  const changed = gitDiff.changedFiles || [];
  if (Object.keys(gitDiff).length === 0) {
    summaryDiffEl.textContent = pipeline.gitDiff;
  } else {
    const diffBits = [
      gitDiff.hasChanges ? '변경 있음' : '변경 없음',
      gitDiff.saved ? `저장됨: ${gitDiff.path}` : '저장된 diff 없음'
    ];
    if (changed.length > 0) {
      diffBits.push(`파일: ${changed.join(', ')}`);
    }
    summaryDiffEl.textContent = diffBits.join(' / ');
  }

  const review = summary.review || {};
  summaryReviewEl.textContent = review.file
    ? `${review.status}: ${review.file}${review.decision ? ` / ${review.decision}` : ''}`
    : review.status || pipeline.reviewStatus;
  summaryNextActionEl.textContent = pipeline.nextAction || '-';
}

function renderRequirementsText(requirements) {
  if (!requirements || !requirements.files || requirements.files.length === 0) {
    return '';
  }
  const lines = [
    `필수 파일 (${requirements.label || '현재 단계'}):`,
    ...requirements.files.map((file) => `- ${file.name}: ${file.exists ? 'ready' : 'missing'}`),
    `다음 단계 가능: ${requirements.nextStageAllowed ? 'yes' : 'no'}`
  ];
  return lines.join('\n');
}

function hasArtifact(pipeline, name) {
  return (pipeline?.artifacts || []).some((artifact) => (artifact.name || artifact) === name);
}

function updateSendButtonGates(pipeline) {
  sendButtons.forEach((button) => {
    const target = button.dataset.send;
    let disabled = false;
    let title = '';
    if (!pipeline) {
      disabled = false;
    } else if (target === 'codex-implement') {
      disabled = !hasArtifact(pipeline, 'plan.md') || !hasArtifact(pipeline, 'codex-task.md');
      title = disabled ? 'Claude 계획이 아직 완료되지 않았습니다. plan.md와 codex-task.md가 생성된 뒤 Codex를 실행할 수 있습니다.' : '';
    } else if (target === 'claude-review') {
      disabled = !hasArtifact(pipeline, 'patch.md');
      title = disabled ? 'patch.md가 생성된 뒤 Claude 리뷰를 실행할 수 있습니다.' : '';
    } else if (target === 'codex-review-fix') {
      disabled = pipeline.state !== 'review_changes_requested';
      title = disabled ? 'Claude가 수정 요청을 남긴 뒤 실행할 수 있습니다.' : '';
    } else if (target === 'claude-re-review') {
      disabled = !hasArtifact(pipeline, 'status.md');
      title = disabled ? 'Codex 리뷰 반영 후 status.md가 생성된 뒤 실행할 수 있습니다.' : '';
    }
    button.disabled = disabled;
    button.title = title;
  });
}

function getApprovalRequest(status, pipeline) {
  const issue = pipeline.detectedIssue || {};
  const isApproval = pipeline.state === 'approval_required' || issue.type === 'approval_required';
  if (!isApproval) {
    return null;
  }

  const targetWindow = issue.window || pipeline.targetWindow;
  const stageTargetWindow = stageWindows[pipeline.step] || pipeline.targetWindow || targetWindow;
  if (!['claude', 'codex'].includes(stageTargetWindow)) {
    return null;
  }

  const jobId = status.jobId || jobIdEl.value.trim() || '-';
  const step = pipeline.step || '-';
  const approvalContext = issue.approvalContext || null;
  const rawSummary = approvalContext?.rawBlock || issue.summary || pipeline.message || '';
  const summary = approvalContext?.summary || cleanApprovalSummary(stageTargetWindow);
  const key = `${jobId}:${step}:${stageTargetWindow}:${rawSummary || summary}`;
  return { key, step, targetWindow: stageTargetWindow, summary, approvalContext };
}

function cleanApprovalSummary(windowName) {
  const label = windowName === 'codex' ? 'Codex' : 'Claude';
  return `${label} 창에서 승인 대기 문구가 감지되었습니다.`;
}

function openApprovalModal(request, force) {
  currentApprovalRequest = request;
  if (!force && lastApprovalKey === request.key) {
    return;
  }
  lastApprovalKey = request.key;
  renderApprovalContext(request, request.approvalContext);
  approvalModalEl.hidden = false;
  if (!request.approvalContext) {
    loadApprovalContext(request);
  }
}

async function loadApprovalContext(request) {
  try {
    const result = await requestJson(`/api/tmux/approval-context?window=${encodeURIComponent(request.targetWindow)}&step=${encodeURIComponent(request.step || '')}`);
    if (!currentApprovalRequest || currentApprovalRequest.key !== request.key) {
      return;
    }
    currentApprovalRequest.approvalContext = result.approvalContext;
    renderApprovalContext(currentApprovalRequest, result.approvalContext);
  } catch (error) {
    approvalModalRawEl.textContent = error.message;
  }
}

function renderApprovalContext(request, context) {
  const risk = context?.risk || 'unknown';
  approvalModalStepEl.textContent = request.step || context?.step || '-';
  approvalModalWindowEl.textContent = request.targetWindow || context?.window || '-';
  approvalModalSummaryEl.textContent = context?.summary || request.summary || '-';
  approvalModalTypeEl.textContent = context?.type || 'unknown';
  approvalModalCommandEl.textContent = context?.commandOrTarget || '확인 불가';
  approvalModalCwdEl.textContent = context?.workingDirectory || '-';
  approvalModalRiskEl.textContent = risk;
  approvalModalRiskEl.dataset.risk = risk;
  approvalModalRecommendationEl.textContent = context?.recommendation || '직접 확인 필요';
  approvalModalRawEl.textContent = context?.rawBlock || '원문을 불러오는 중입니다.';
  approvalModalRiskWarningEl.textContent = context?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.';
  approvalModalApproveOnceEl.disabled = !context?.canApproveOnce;
  approvalModalApproveSessionEl.disabled = !context?.canApproveSession;
}

function closeApprovalModal() {
  approvalModalEl.hidden = true;
}

async function sendApprovalModalAction(endpoint) {
  if (!currentApprovalRequest || !['claude', 'codex'].includes(currentApprovalRequest.targetWindow)) {
    writeOutput('승인 명령 실패', '승인 대상 창을 확인할 수 없습니다.');
    return;
  }
  if (!approvalEndpointAllowed(endpoint, currentApprovalRequest.approvalContext)) {
    writeOutput('승인 명령 차단', currentApprovalRequest.approvalContext?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.');
    return;
  }

  try {
    await requestJson(endpoint, {
      method: 'POST',
      body: JSON.stringify({ window: currentApprovalRequest.targetWindow })
    });
    closeApprovalModal();
    writeOutput('승인 명령', '명령을 전송했습니다. 상태를 다시 확인합니다.');
    setTimeout(refreshPipelineStatus, 1000);
  } catch (error) {
    writeOutput('승인 명령 실패', error.message);
  }
}

function approvalEndpointAllowed(endpoint, context) {
  if (endpoint.endsWith('/approve-once')) {
    return Boolean(context?.canApproveOnce);
  }
  if (endpoint.endsWith('/approve-session')) {
    return Boolean(context?.canApproveSession);
  }
  return true;
}

function normalizePipelineStatus(payload) {
  if (payload && payload.status && typeof payload.status === 'object') {
    return {
      state: payload.status.state || 'idle',
      message: payload.status.message || '',
      step: payload.status.step || null,
      targetWindow: payload.status.targetWindow || null,
      waitingApproval: Boolean(payload.status.waitingApproval),
      detectedIssue: payload.status.detectedIssue || null,
      artifacts: payload.status.artifacts || [],
      requirements: payload.status.requirements || null,
      gitDiff: payload.status.gitDiff || '-',
      reviewStatus: payload.status.reviewStatus || '-',
      nextAction: payload.status.nextAction || '-'
    };
  }

  return {
    state: payload && payload.status ? payload.status : 'idle',
    message: payload && payload.error ? payload.error : '',
    step: payload && payload.currentStep ? payload.currentStep : null,
    targetWindow: null,
    waitingApproval: false,
    detectedIssue: null,
    artifacts: payload && payload.artifacts ? payload.artifacts : [],
    requirements: null,
    gitDiff: '-',
    reviewStatus: '-',
    nextAction: '-'
  };
}

function renderDetectedIssue(issue) {
  if (!issue) {
    detectedIssueAlertEl.hidden = true;
    detectedIssueAlertEl.textContent = '';
    detectedIssueAlertEl.dataset.type = '';
    return;
  }

  const message = detectedIssueMessages[issue.type] || issue.recommendation || 'AI CLI 출력에서 확인이 필요한 상태가 감지되었습니다.';
  const parts = [
    message,
    issue.window ? `창: ${issue.window}` : '',
    issue.summary ? `감지 내용: ${issue.summary}` : ''
  ].filter(Boolean);
  detectedIssueAlertEl.textContent = parts.join('\n');
  detectedIssueAlertEl.dataset.type = issue.type || 'manual_review_required';
  detectedIssueAlertEl.hidden = false;
}

async function loadTmuxWindows() {
  const result = await runAction('tmux 창 목록', () => requestJson('/api/tmux/windows'));
  tmuxWindowEl.textContent = '';
  const windows = result && result.windows ? result.windows : [];
  windows.forEach((windowInfo) => {
    const option = document.createElement('option');
    option.value = windowInfo.name;
    option.dataset.aiRole = windowInfo.aiRole ? 'true' : 'false';
    option.textContent = `${windowInfo.label || windowInfo.name}${windowInfo.available ? '' : ' (세션 없음)'}`;
    tmuxWindowEl.appendChild(option);
  });
  if (!tmuxWindowEl.value && windows.length > 0) {
    tmuxWindowEl.value = windows[0].name;
  }
  updateTmuxControlState();
}

function updateTmuxControlState() {
  const selected = tmuxWindowEl.options[tmuxWindowEl.selectedIndex];
  const isAiRole = !selected || selected.dataset.aiRole !== 'false';
  aiControlButtons.forEach((button) => {
    button.disabled = !isAiRole;
  });
}

async function refreshTmuxOutput() {
  const windowName = tmuxWindowEl.value;
  if (!windowName) {
    tmuxOutputEl.textContent = '표시할 tmux 창이 없습니다.';
    return null;
  }
  try {
    const result = await requestJson(`/api/tmux/output?window=${encodeURIComponent(windowName)}`);
    tmuxOutputEl.textContent = result.output || '(출력 없음)';
    return result;
  } catch (error) {
    tmuxOutputEl.textContent = error.message;
    return null;
  }
}

async function sendTmuxControl(title, endpoint) {
  const windowName = tmuxWindowEl.value;
  if (!windowName) {
    writeOutput(`${title} 실패`, '제어할 tmux 창을 선택하세요.');
    return null;
  }
  const selected = tmuxWindowEl.options[tmuxWindowEl.selectedIndex];
  if (selected && selected.dataset.aiRole === 'false') {
    writeOutput(`${title} 실패`, 'Manual Shell(git-shell)은 비AI 창입니다. 승인/거절 키 입력은 Claude 또는 Codex 창에서만 사용하세요.');
    return null;
  }
  if (currentApprovalRequest && currentApprovalRequest.targetWindow === windowName && !approvalEndpointAllowed(endpoint, currentApprovalRequest.approvalContext)) {
    writeOutput(`${title} 차단`, currentApprovalRequest.approvalContext?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.');
    return null;
  }
  const result = await runAction(title, () => requestJson(endpoint, {
    method: 'POST',
    body: JSON.stringify({ window: windowName })
  }));
  refreshTmuxOutput();
  return result;
}

loadTmuxWindows().then(startLiveRefresh);

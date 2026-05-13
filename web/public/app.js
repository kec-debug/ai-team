const state = {
  projectDir: localStorage.getItem('aiTeamProjectDir') || '',
  jobId: localStorage.getItem('aiTeamJobId') || 'job-002'
};

const projectDirEl = document.querySelector('#projectDir');
const jobIdEl = document.querySelector('#jobId');
const inputKoEl = document.querySelector('#inputKo');
const outputEl = document.querySelector('#output');
const artifactListEl = document.querySelector('#artifactList');
const runPipelineButton = document.querySelector('#runPipeline');
const pipelineStateEl = document.querySelector('#pipelineState');
const pipelineJobIdEl = document.querySelector('#pipelineJobId');
const pipelineStageEl = document.querySelector('#pipelineStage');
const pipelineStateNameEl = document.querySelector('#pipelineStateName');
const pipelineUpdatedAtEl = document.querySelector('#pipelineUpdatedAt');
const pipelineTargetWindowEl = document.querySelector('#pipelineTargetWindow');
const pipelineWaitingApprovalEl = document.querySelector('#pipelineWaitingApproval');
const pipelineGuidanceEl = document.querySelector('#pipelineGuidance');
const pipelineStepsEl = document.querySelector('#pipelineSteps');
const summaryArtifactsEl = document.querySelector('#summaryArtifacts');
const summaryDiffEl = document.querySelector('#summaryDiff');
const summaryReviewEl = document.querySelector('#summaryReview');
const summaryNextActionEl = document.querySelector('#summaryNextAction');
const tmuxWindowEl = document.querySelector('#tmuxWindow');
const tmuxOutputEl = document.querySelector('#tmuxOutput');
let pipelinePollTimer = null;
let liveRefreshTimer = null;
const manualRequiredMessage = 'AI CLI 창에서 승인 대기 중일 수 있습니다. 아래 승인 버튼을 누르거나 tmux 출력을 확인하세요.';

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
  runAction('input.ko.md 저장', () => requestJson('/api/save-input', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
});

runPipelineButton.addEventListener('click', async () => {
  const result = await runAction('전체 파이프라인 실행', () => requestJson('/api/pipeline/run', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
  if (result) {
    startPipelinePolling();
  }
});

document.querySelector('#pipelineStatus').addEventListener('click', refreshPipelineStatus);

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
document.querySelector('#refreshTmuxOutput').addEventListener('click', refreshTmuxOutput);
tmuxWindowEl.addEventListener('change', refreshTmuxOutput);

document.querySelector('#restartAiTeam').addEventListener('click', () => {
  runAction('AI팀 재시작', () => requestJson('/api/service/restart-ai-team', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
});

document.querySelector('#restartGui').addEventListener('click', () => {
  runAction('GUI 서버 재시작', () => requestJson('/api/service/restart-gui', {
    method: 'POST',
    body: JSON.stringify(getForm())
  }));
});

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
    if (pipelinePollTimer && ['succeeded', 'failed', 'blocked_safety', 'manual_required', 'idle'].includes(pipeline.state)) {
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
    pipelineGuidanceEl.hidden = true;
    pipelineGuidanceEl.textContent = '';
    pipelineStepsEl.textContent = '';
    summaryArtifactsEl.textContent = '-';
    summaryDiffEl.textContent = '-';
    summaryReviewEl.textContent = '-';
    runPipelineButton.disabled = false;
    return;
  }

  const pipeline = normalizePipelineStatus(status);
  const currentForm = getForm();
  const current = pipeline.step ? ` / 현재 단계: ${pipeline.step}` : '';
  pipelineStateEl.textContent = `${pipeline.state}: ${pipeline.message}${current}`;
  pipelineStateEl.dataset.status = pipeline.state;
  runPipelineButton.disabled = pipeline.state === 'running';
  pipelineJobIdEl.textContent = status.jobId || currentForm.jobId || '-';
  pipelineStageEl.textContent = pipeline.step || '-';
  pipelineStateNameEl.textContent = pipeline.state;
  pipelineUpdatedAtEl.textContent = status.updatedAt ? new Date(status.updatedAt).toLocaleTimeString('ko-KR', { hour12: false }) : '-';
  pipelineTargetWindowEl.textContent = pipeline.targetWindow || '-';
  pipelineWaitingApprovalEl.textContent = pipeline.waitingApproval ? '예' : '아니오';

  if (pipeline.targetWindow && tmuxWindowEl.value !== pipeline.targetWindow) {
    tmuxWindowEl.value = pipeline.targetWindow;
    refreshTmuxOutput();
  }

  if (pipeline.state === 'manual_required' || pipeline.state === 'waiting_approval') {
    pipelineGuidanceEl.hidden = false;
    pipelineGuidanceEl.textContent = pipeline.message || manualRequiredMessage;
  } else {
    pipelineGuidanceEl.hidden = true;
    pipelineGuidanceEl.textContent = '';
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

function normalizePipelineStatus(payload) {
  if (payload && payload.status && typeof payload.status === 'object') {
    return {
      state: payload.status.state || 'idle',
      message: payload.status.message || '',
      step: payload.status.step || null,
      targetWindow: payload.status.targetWindow || null,
      waitingApproval: Boolean(payload.status.waitingApproval),
      artifacts: payload.status.artifacts || [],
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
    artifacts: payload && payload.artifacts ? payload.artifacts : [],
    gitDiff: '-',
    reviewStatus: '-',
    nextAction: '-'
  };
}

async function loadTmuxWindows() {
  const result = await runAction('tmux 창 목록', () => requestJson('/api/tmux/windows'));
  tmuxWindowEl.textContent = '';
  const windows = result && result.windows ? result.windows : [];
  windows.forEach((windowInfo) => {
    const option = document.createElement('option');
    option.value = windowInfo.name;
    option.textContent = `${windowInfo.name}${windowInfo.available ? '' : ' (세션 없음)'}`;
    tmuxWindowEl.appendChild(option);
  });
  if (!tmuxWindowEl.value && windows.length > 0) {
    tmuxWindowEl.value = windows[0].name;
  }
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
  const result = await runAction(title, () => requestJson(endpoint, {
    method: 'POST',
    body: JSON.stringify({ window: windowName })
  }));
  refreshTmuxOutput();
  return result;
}

loadTmuxWindows().then(startLiveRefresh);

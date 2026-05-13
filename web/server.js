const express = require('express');
const fs = require('fs/promises');
const path = require('path');
const { execFile } = require('child_process');

const app = express();
const HOST = process.env.HOST || '127.0.0.1';
const PORT = Number(process.env.PORT || 3100);
const SESSION = 'ai-team';
const ROOT_DIR = path.resolve(__dirname, '..');
const SCRIPTS_DIR = path.join(ROOT_DIR, 'scripts');
const SAFE_WINDOWS = {
  gemini: 'gemini-manager',
  'claude-architect': 'claude-architect',
  codex: 'codex-implementer',
  'claude-reviewer': 'claude-reviewer'
};
const ALLOWED_TMUX_WINDOWS = new Set([
  'gemini-manager',
  'claude-architect',
  'codex-implementer',
  'claude-reviewer',
  'git-shell'
]);
const PIPELINE_STEP_TIMEOUT_MS = Number(process.env.AI_TEAM_PIPELINE_STEP_TIMEOUT_MS || 15 * 60 * 1000);
const PIPELINE_POLL_MS = Number(process.env.AI_TEAM_PIPELINE_POLL_MS || 5000);
const MANUAL_REQUIRED_MESSAGE = 'AI CLI 창에서 승인 대기 중일 수 있습니다. 아래 승인 버튼을 누르거나 tmux 출력을 확인하세요.';
const pipelineStates = new Map();
const PIPELINE_STAGES = [
  { id: 'gemini', label: 'Gemini Manager', role: 'gemini', window: 'gemini-manager', artifacts: ['gemini-plan.en.md', 'codex-prompt.en.md'] },
  { id: 'claude-architect', label: 'Claude Architect', role: 'claude-architect', window: 'claude-architect', artifacts: ['claude-design-review.en.md', 'architecture.md'] },
  { id: 'codex', label: 'Codex Implementer', role: 'codex', window: 'codex-implementer', artifacts: ['codex-summary.en.md'] },
  { id: 'claude-reviewer', label: 'Claude Reviewer', role: 'claude-reviewer', window: 'claude-reviewer', artifacts: ['claude-pr-review.en.md', 'review.md'] }
];
const ARTIFACT_NAMES = new Set([
  'README.md',
  'input.ko.md',
  'input.en.md',
  'plan.en.md',
  'gemini-plan.en.md',
  'architecture.md',
  'claude-design-review.en.md',
  'codex-prompt.en.md',
  'patch.md',
  'codex-summary.en.md',
  'review.md',
  'claude-pr-review.en.md',
  'local-diff.patch',
  'pipeline.log.md'
]);
const SAFETY_DENY_PATTERNS = [
  /^\.env(?:\.|$)/,
  /(^|\/)secrets?\//,
  /(^|\/)migrations?\//,
  /(^|\/)auth\//,
  /(^|\/)payment\//,
  /(^|\/)billing\//,
  /^infra\//,
  /^\.github\/workflows\//
];

app.use(express.json({ limit: '1mb' }));
app.use(express.static(path.join(__dirname, 'public')));

function runFile(file, args, options = {}) {
  return new Promise((resolve) => {
    execFile(file, args, { timeout: 30000, maxBuffer: 1024 * 1024, ...options }, (error, stdout, stderr) => {
      resolve({
        ok: !error,
        code: error && typeof error.code === 'number' ? error.code : 0,
        stdout,
        stderr,
        message: error ? error.message : ''
      });
    });
  });
}

async function resolveProjectDir(projectDir) {
  if (!projectDir || typeof projectDir !== 'string') {
    throw new Error('프로젝트 경로가 필요합니다.');
  }

  const resolved = path.resolve(projectDir);
  const stat = await fs.stat(resolved).catch(() => null);
  if (!stat || !stat.isDirectory()) {
    throw new Error('프로젝트 경로가 존재하지 않거나 디렉터리가 아닙니다.');
  }

  return resolved;
}

function validateJobId(jobId) {
  if (!jobId || typeof jobId !== 'string' || !/^[A-Za-z0-9._-]+$/.test(jobId)) {
    throw new Error('작업 ID는 영문, 숫자, 점, 밑줄, 하이픈만 사용할 수 있습니다.');
  }
  return jobId;
}

function resolveInside(baseDir, requestedPath) {
  if (!requestedPath || typeof requestedPath !== 'string') {
    throw new Error('파일 경로가 필요합니다.');
  }

  const absolute = path.resolve(baseDir, requestedPath);
  const relative = path.relative(baseDir, absolute);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new Error('선택한 프로젝트 밖의 파일은 읽을 수 없습니다.');
  }
  return absolute;
}

function resolveJobArtifact(projectDir, requestedPath) {
  const absolute = resolveInside(projectDir, requestedPath);
  const relative = path.relative(projectDir, absolute);
  const parts = relative.split(path.sep);
  if (parts.length < 5 || parts[0] !== 'docs' || parts[1] !== 'ai' || parts[2] !== 'jobs') {
    throw new Error('작업 산출물 경로만 읽을 수 있습니다.');
  }
  return absolute;
}

function cleanOutput(result) {
  return {
    ok: result.ok,
    code: result.code,
    output: `${result.stdout || ''}${result.stderr || ''}`,
    message: result.message
  };
}

function redactedOutput(text) {
  return String(text || '')
    .replace(/\bsk-[A-Za-z0-9_-]{12,}\b/g, '[REDACTED_OPENAI_KEY]')
    .replace(/\bgh[pousr]_[A-Za-z0-9_]{12,}\b/g, '[REDACTED_GITHUB_TOKEN]')
    .replace(/\bxox[baprs]-[A-Za-z0-9-]{12,}\b/g, '[REDACTED_SLACK_TOKEN]')
    .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]{12,}/gi, 'Bearer [REDACTED]');
}

function pipelineKey(projectDir, jobId) {
  return `${projectDir}::${jobId}`;
}

function validateTmuxWindow(windowName) {
  if (!windowName || typeof windowName !== 'string' || !ALLOWED_TMUX_WINDOWS.has(windowName)) {
    throw new Error('허용되지 않은 tmux 창입니다.');
  }
  return windowName;
}

function stageById(stageId) {
  return PIPELINE_STAGES.find((stage) => stage.id === stageId) || null;
}

function currentTargetWindow(state) {
  const stage = stageById(state.currentStep);
  return stage ? stage.window : null;
}

function publicIdlePipelineState(projectDir = null, jobId = null) {
  const now = new Date().toISOString();
  return {
    ok: true,
    jobKey: projectDir && jobId ? pipelineKey(projectDir, jobId) : null,
    projectDir,
    jobId,
    updatedAt: now,
    status: {
      state: 'idle',
      message: '아직 실행되지 않았습니다.',
      step: null,
      targetWindow: null,
      waitingApproval: false,
      artifacts: [],
      gitDiff: '-',
      reviewStatus: '-',
      nextAction: '작업 요청을 입력한 뒤 전체 파이프라인 실행을 누르세요.'
    }
  };
}

function publicPipelineState(state) {
  if (!state) {
    return publicIdlePipelineState();
  }

  const gitDiff = state.summary.gitDiff;
  const gitDiffText = gitDiff.hasChanges
    ? `변경 있음${gitDiff.saved && gitDiff.path ? ` / 저장됨: ${gitDiff.path}` : ''}`
    : '-';
  const review = state.summary.review;
  const reviewStatus = review.file
    ? `${review.status}: ${review.file}${review.decision ? ` / ${review.decision}` : ''}`
    : review.status || '-';

  return {
    ok: true,
    jobKey: state.jobKey,
    projectDir: state.projectDir,
    jobId: state.jobId,
    startedAt: state.startedAt,
    finishedAt: state.finishedAt,
    updatedAt: state.updatedAt,
    error: state.error,
    status: {
      state: state.status,
      message: state.error || pipelineMessage(state.status),
      step: state.currentStep,
      targetWindow: currentTargetWindow(state),
      waitingApproval: state.status === 'waiting_approval' || state.status === 'manual_required',
      artifacts: state.artifacts,
      gitDiff: gitDiffText,
      reviewStatus,
      nextAction: nextRecommendedAction(state, reviewStatus)
    },
    steps: state.steps,
    artifacts: state.artifacts,
    summary: state.summary
  };
}

function pipelineMessage(status) {
  if (status === 'running') {
    return '파이프라인 실행 중입니다.';
  }
  if (status === 'succeeded') {
    return '파이프라인이 완료되었습니다.';
  }
  if (status === 'failed') {
    return '파이프라인 실행에 실패했습니다.';
  }
  if (status === 'blocked_safety') {
    return '안전 정책에 따라 파이프라인이 중단되었습니다.';
  }
  if (status === 'waiting_approval') {
    return MANUAL_REQUIRED_MESSAGE;
  }
  if (status === 'manual_required') {
    return MANUAL_REQUIRED_MESSAGE;
  }
  return '아직 실행되지 않았습니다.';
}

function nextRecommendedAction(state, reviewStatus) {
  if (state.status === 'succeeded') {
    return reviewStatus && reviewStatus !== '-'
      ? 'Reviewer 결과를 확인한 뒤 사람이 직접 commit, push, PR 생성 여부를 결정하세요.'
      : '산출물과 git diff를 확인한 뒤 사람이 직접 다음 작업을 결정하세요.';
  }
  if (state.status === 'manual_required' || state.status === 'waiting_approval') {
    return 'tmux 출력을 확인하고 필요한 경우 승인 / 계속 진행, 세션 승인, 거절, 중단 중 하나를 선택하세요.';
  }
  if (state.status === 'failed') {
    return '오류 메시지와 tmux 출력을 확인한 뒤 상태 초기화 또는 수동 복구를 진행하세요.';
  }
  if (state.status === 'running') {
    return '현재 단계의 tmux 출력을 보면서 진행 상황을 확인하세요.';
  }
  return '전체 파이프라인 실행을 시작하세요.';
}

function createPipelineState(projectDir, jobId) {
  const now = new Date().toISOString();
  const key = pipelineKey(projectDir, jobId);
  return {
    jobKey: key,
    projectDir,
    jobId,
    status: 'running',
    currentStep: 'queued',
    startedAt: now,
    finishedAt: null,
    updatedAt: now,
    error: null,
    steps: [],
    artifacts: [],
    summary: {
      createdArtifacts: [],
      gitDiff: { hasChanges: false, saved: false, path: null, changedFiles: [] },
      review: { status: 'not_started', file: null, decision: null }
    }
  };
}

function setStep(state, id, label, status, detail = '') {
  const now = new Date().toISOString();
  let step = state.steps.find((item) => item.id === id);
  if (!step) {
    step = { id, label, status, detail: '', startedAt: now, finishedAt: null };
    state.steps.push(step);
  }
  step.status = status;
  step.detail = detail;
  if (status === 'running') {
    step.startedAt = now;
    step.finishedAt = null;
  }
  if (['succeeded', 'failed', 'blocked_safety', 'manual_required', 'waiting_approval'].includes(status)) {
    step.finishedAt = now;
  }
  state.currentStep = status === 'running' ? id : state.currentStep;
  state.updatedAt = now;
}

async function appendPipelineLog(projectDir, jobId, title, body) {
  const logPath = path.join(projectDir, 'docs', 'ai', 'jobs', jobId, 'pipeline.log.md');
  const section = [
    `\n## ${new Date().toISOString()} — ${title}`,
    '',
    '```',
    redactedOutput(body || '(no output)'),
    '```',
    ''
  ].join('\n');
  await fs.appendFile(logPath, section, 'utf8');
}

async function listArtifacts(projectDir, jobId) {
  const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
  const entries = await fs.readdir(jobDir, { withFileTypes: true }).catch(() => []);
  return entries
    .filter((entry) => entry.isFile() && ARTIFACT_NAMES.has(entry.name))
    .map((entry) => {
      const relativePath = path.join('docs', 'ai', 'jobs', jobId, entry.name);
      return { name: entry.name, path: relativePath };
    })
    .sort((a, b) => a.name.localeCompare(b.name));
}

async function refreshPipelineArtifacts(state) {
  state.artifacts = await listArtifacts(state.projectDir, state.jobId);
  state.summary.createdArtifacts = state.artifacts.map((artifact) => artifact.name);
  state.updatedAt = new Date().toISOString();
}

async function findFirstExistingArtifact(projectDir, jobId, names) {
  for (const name of names) {
    const filePath = path.join(projectDir, 'docs', 'ai', 'jobs', jobId, name);
    const stat = await fs.stat(filePath).catch(() => null);
    if (stat && stat.isFile() && stat.size > 0) {
      return { name, path: filePath };
    }
  }
  return null;
}

async function waitForArtifact(projectDir, jobId, names, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const artifact = await findFirstExistingArtifact(projectDir, jobId, names);
    if (artifact) {
      return artifact;
    }
    await new Promise((resolve) => setTimeout(resolve, PIPELINE_POLL_MS));
  }
  return null;
}

function markManualRequired(state, stepId, label) {
  state.status = 'manual_required';
  state.finishedAt = new Date().toISOString();
  state.updatedAt = state.finishedAt;
  state.error = MANUAL_REQUIRED_MESSAGE;
  setStep(state, stepId, label, 'manual_required', MANUAL_REQUIRED_MESSAGE);
}

function markTimedOutRunningStep(state) {
  if (!['running', 'waiting_approval'].includes(state.status) || !state.currentStep) {
    return;
  }
  const running = state.steps.find((step) => step.id === state.currentStep && step.status === 'running');
  if (!running) {
    return;
  }
  const startedAt = Date.parse(running.startedAt);
  if (Number.isNaN(startedAt) || Date.now() - startedAt < PIPELINE_STEP_TIMEOUT_MS) {
    return;
  }
  markManualRequired(state, running.id, running.label);
}

function looksLikeApprovalPrompt(output) {
  return /approval|approve|allow|continue|proceed|permission|승인|허용|계속|진행|거절|reject|1\)|2\)|3\)/i.test(output || '');
}

async function refreshApprovalState(state) {
  if (!state || state.status !== 'running') {
    return;
  }
  const targetWindow = currentTargetWindow(state);
  if (!targetWindow) {
    return;
  }
  const result = await runFile('tmux', ['capture-pane', '-p', '-S', '-80', '-t', `${SESSION}:${targetWindow}`], {
    timeout: 10000,
    maxBuffer: 256 * 1024
  });
  if (result.ok && looksLikeApprovalPrompt(result.stdout)) {
    state.status = 'waiting_approval';
    state.error = MANUAL_REQUIRED_MESSAGE;
    state.updatedAt = new Date().toISOString();
  }
}

async function applyArtifactProgress(state) {
  if (!state || !['running', 'waiting_approval'].includes(state.status)) {
    return;
  }

  for (const stage of PIPELINE_STAGES) {
    const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, stage.artifacts);
    const step = state.steps.find((item) => item.id === stage.id);
    if (artifact && step && step.status === 'running') {
      state.status = 'running';
      state.error = null;
      setStep(state, stage.id, stage.label, 'succeeded', artifact.name);
    }
  }

  const current = stageById(state.currentStep);
  if (current) {
    const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, current.artifacts);
    if (artifact) {
      state.status = 'running';
      state.error = null;
      setStep(state, current.id, current.label, 'succeeded', artifact.name);
    }
  }
}

function isDeniedSafetyPath(filePath) {
  return SAFETY_DENY_PATTERNS.some((pattern) => pattern.test(filePath));
}

async function changedFiles(projectDir) {
  const result = await runFile('git', ['diff', '--name-only', '--', '.'], { cwd: projectDir });
  if (!result.ok) {
    return [];
  }
  return result.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

async function saveLocalDiff(projectDir, jobId, state) {
  const result = await runFile('git', ['diff', '--', '.'], {
    cwd: projectDir,
    timeout: 30000,
    maxBuffer: 5 * 1024 * 1024
  });
  const diffPath = path.join(projectDir, 'docs', 'ai', 'jobs', jobId, 'local-diff.patch');
  const output = result.ok ? result.stdout : `${result.stdout || ''}${result.stderr || ''}`;
  if (output.trim()) {
    await fs.writeFile(diffPath, output, 'utf8');
  }
  const files = await changedFiles(projectDir);
  state.summary.gitDiff = {
    hasChanges: Boolean(output.trim()),
    saved: Boolean(output.trim()),
    path: output.trim() ? path.join('docs', 'ai', 'jobs', jobId, 'local-diff.patch') : null,
    changedFiles: files
  };
  return result;
}

async function updateGitDiffSummary(projectDir, jobId, state) {
  const result = await runFile('git', ['diff', '--', '.'], {
    cwd: projectDir,
    timeout: 30000,
    maxBuffer: 5 * 1024 * 1024
  });
  const files = await changedFiles(projectDir);
  const hasChanges = result.ok && Boolean(result.stdout.trim());
  const diffPath = path.join(projectDir, 'docs', 'ai', 'jobs', jobId, 'local-diff.patch');
  const saved = Boolean(await fs.stat(diffPath).catch(() => null));
  state.summary.gitDiff = {
    hasChanges,
    saved,
    path: saved ? path.join('docs', 'ai', 'jobs', jobId, 'local-diff.patch') : null,
    changedFiles: files
  };
}

async function updateReviewSummary(projectDir, jobId, state) {
  const artifact = await findFirstExistingArtifact(projectDir, jobId, ['claude-pr-review.en.md', 'review.md']);
  if (!artifact) {
    state.summary.review = { status: 'not_found', file: null, decision: null };
    return;
  }
  const content = await fs.readFile(artifact.path, 'utf8').catch(() => '');
  const decisionLine = content.split(/\r?\n/).find((line) => /decision|verdict|approve|request changes|comment/i.test(line));
  state.summary.review = {
    status: 'available',
    file: artifact.name,
    decision: decisionLine ? decisionLine.trim() : null
  };
}

async function runPipeline(state, inputKo) {
  const { projectDir, jobId } = state;
  const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
  try {
    setStep(state, 'create-job', '작업 폴더 생성', 'running');
    await fs.mkdir(jobDir, { recursive: true });
    await appendPipelineLog(projectDir, jobId, 'create-job', `Ensured job directory: ${jobDir}`);
    setStep(state, 'create-job', '작업 폴더 생성', 'succeeded', jobDir);

    setStep(state, 'save-input', 'input.ko.md 저장', 'running');
    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'input.ko.md'));
    await fs.writeFile(inputPath, inputKo, 'utf8');
    await appendPipelineLog(projectDir, jobId, 'save-input', `Saved: ${inputPath}`);
    setStep(state, 'save-input', 'input.ko.md 저장', 'succeeded', inputPath);
    await refreshPipelineArtifacts(state);

    for (const step of PIPELINE_STAGES.slice(0, 3)) {
      state.status = 'running';
      state.error = null;
      setStep(state, step.id, step.label, 'running');
      const sent = await sendToWindow(step.role, projectDir, jobId, inputKo);
      await appendPipelineLog(projectDir, jobId, step.id, `${sent.stdout || ''}${sent.stderr || ''}${sent.message || ''}`);
      if (!sent.ok) {
        throw new Error(`${step.label} 실패: ${sent.message || sent.stderr || 'tmux 전송 실패'}`);
      }
      const artifact = await waitForArtifact(projectDir, jobId, step.artifacts);
      if (!artifact) {
        markManualRequired(state, step.id, step.label);
        await refreshPipelineArtifacts(state);
        return;
      }
      state.status = 'running';
      state.error = null;
      setStep(state, step.id, step.label, 'succeeded', artifact.name);
      await refreshPipelineArtifacts(state);

      if (step.id === 'codex') {
        const denied = (await changedFiles(projectDir)).filter(isDeniedSafetyPath);
        if (denied.length > 0) {
          state.status = 'blocked_safety';
          state.finishedAt = new Date().toISOString();
          state.error = `안전 차단 경로 변경 감지: ${denied.join(', ')}`;
          setStep(state, 'safety-check', '안전 경로 확인', 'blocked_safety', state.error);
          await appendPipelineLog(projectDir, jobId, 'safety-check', state.error);
          await refreshPipelineArtifacts(state);
          return;
        }
      }
    }

    setStep(state, 'save-diff', 'git diff 저장', 'running');
    const diffResult = await saveLocalDiff(projectDir, jobId, state);
    await appendPipelineLog(projectDir, jobId, 'save-diff', `${diffResult.stdout || ''}${diffResult.stderr || ''}${diffResult.message || ''}`);
    setStep(state, 'save-diff', 'git diff 저장', 'succeeded', state.summary.gitDiff.saved ? 'local-diff.patch' : '변경 없음');
    await refreshPipelineArtifacts(state);

    const reviewerStep = PIPELINE_STAGES[3];
    state.status = 'running';
    state.error = null;
    setStep(state, reviewerStep.id, reviewerStep.label, 'running');
    const reviewed = await sendToWindow(reviewerStep.role, projectDir, jobId, inputKo);
    await appendPipelineLog(projectDir, jobId, 'claude-reviewer', `${reviewed.stdout || ''}${reviewed.stderr || ''}${reviewed.message || ''}`);
    if (!reviewed.ok) {
      throw new Error(`Claude Reviewer 전송 실패: ${reviewed.message || reviewed.stderr || 'tmux 전송 실패'}`);
    }
    const reviewArtifact = await waitForArtifact(projectDir, jobId, reviewerStep.artifacts);
    if (!reviewArtifact) {
      markManualRequired(state, reviewerStep.id, reviewerStep.label);
      await updateReviewSummary(projectDir, jobId, state);
      await refreshPipelineArtifacts(state);
      return;
    }
    state.status = 'running';
    state.error = null;
    setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifact.name);
    await updateReviewSummary(projectDir, jobId, state);
    await refreshPipelineArtifacts(state);

    state.status = 'succeeded';
    state.currentStep = null;
    state.finishedAt = new Date().toISOString();
  } catch (error) {
    state.status = 'failed';
    state.error = error.message || '파이프라인 실행 실패';
    state.finishedAt = new Date().toISOString();
    if (state.currentStep) {
      const running = state.steps.find((step) => step.id === state.currentStep && step.status === 'running');
      if (running) {
        setStep(state, running.id, running.label, 'failed', state.error);
      }
    }
    await appendPipelineLog(projectDir, jobId, 'failed', state.error).catch(() => {});
    await refreshPipelineArtifacts(state).catch(() => {});
  }
}

function buildPrompt(role, projectDir, jobId, inputKo) {
  const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
  const common = [
    `Project directory: ${projectDir}`,
    `Job ID: ${jobId}`,
    `Job directory: ${jobDir}`
  ].join('\n');

  if (role === 'gemini') {
    return [
      'Use prompts/gemini-manager.md.',
      common,
      '',
      'Read the Korean job input below and write the English plan into the job directory.',
      '',
      inputKo || `(Read from ${path.join(jobDir, 'input.ko.md')})`
    ].join('\n');
  }

  if (role === 'claude-architect') {
    return [
      'Use prompts/claude-architect.md.',
      common,
      '',
      'Review the plan and write the architecture review into the job directory. Only approve if the design is safe and scoped.'
    ].join('\n');
  }

  if (role === 'codex') {
    return [
      'Use prompts/codex-implementer.md.',
      common,
      '',
      'Implement only the approved job scope. Do not commit, push, merge, or change secrets, .env, auth, payment, production infra, or database migrations.'
    ].join('\n');
  }

  return [
    'Use prompts/claude-reviewer.md.',
    common,
    '',
    'Review the current diff for this job and write the review into the job directory. Do not commit, push, or merge.'
  ].join('\n');
}

async function sendToWindow(role, projectDir, jobId, inputKo) {
  const windowName = SAFE_WINDOWS[role];
  if (!windowName) {
    throw new Error('허용되지 않은 대상입니다.');
  }
  const prompt = buildPrompt(role, projectDir, jobId, inputKo);
  const target = `${SESSION}:${windowName}`;
  const bufferName = 'ai-team-gui-prompt';
  const setBuffer = await runFile('tmux', ['set-buffer', '-b', bufferName, prompt]);
  if (!setBuffer.ok) {
    return setBuffer;
  }
  const pasteBuffer = await runFile('tmux', ['paste-buffer', '-b', bufferName, '-t', target]);
  if (!pasteBuffer.ok) {
    return pasteBuffer;
  }
  return runFile('tmux', ['send-keys', '-t', target, 'Enter']);
}

async function sendKeysToWindow(windowName, keys) {
  const safeWindow = validateTmuxWindow(windowName);
  return runFile('tmux', ['send-keys', '-t', `${SESSION}:${safeWindow}`, ...keys]);
}

async function tmuxSessionRunning(sessionName) {
  const result = await runFile('tmux', ['has-session', '-t', sessionName]);
  return result.ok;
}

function shellQuote(value) {
  return `'${String(value).replace(/'/g, `'\\''`)}'`;
}

function handleError(res, error) {
  res.status(400).json({ ok: false, error: error.message || '요청을 처리할 수 없습니다.' });
}

app.get('/api/status', async (req, res) => {
  const result = await runFile(path.join(SCRIPTS_DIR, 'status-ai-team.sh'), []);
  res.json(cleanOutput(result));
});

app.post('/api/start', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.body.projectDir);
    const result = await runFile(path.join(SCRIPTS_DIR, 'start-ai-team.sh'), [projectDir], {
      cwd: ROOT_DIR,
      env: { ...process.env, TERM: process.env.TERM || 'xterm-256color' }
    });
    res.json(cleanOutput(result));
  } catch (error) {
    handleError(res, error);
  }
});

app.post('/api/create-job', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.body.projectDir);
    const jobId = validateJobId(req.body.jobId);
    const result = await runFile(path.join(SCRIPTS_DIR, 'create-job.sh'), [projectDir, jobId], { cwd: ROOT_DIR });
    res.json(cleanOutput(result));
  } catch (error) {
    handleError(res, error);
  }
});

app.post('/api/save-input', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.body.projectDir);
    const jobId = validateJobId(req.body.jobId);
    const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
    const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
    const target = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'input.ko.md'));
    await fs.mkdir(jobDir, { recursive: true });
    await fs.writeFile(target, inputKo, 'utf8');
    res.json({ ok: true, output: `저장됨: ${target}` });
  } catch (error) {
    handleError(res, error);
  }
});

app.post('/api/pipeline/run', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.body.projectDir);
    const jobId = validateJobId(req.body.jobId);
    const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
    const key = pipelineKey(projectDir, jobId);
    const existing = pipelineStates.get(key);
    if (existing && existing.status === 'running') {
      res.status(409).json({ ok: false, error: '이 작업의 파이프라인이 이미 실행 중입니다.' });
      return;
    }

    const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'input.ko.md'));
    await fs.mkdir(jobDir, { recursive: true });
    await fs.writeFile(inputPath, inputKo, 'utf8');

    const state = createPipelineState(projectDir, jobId);
    pipelineStates.set(key, state);
    void runPipeline(state, inputKo);
    res.json({
      ok: true,
      jobKey: key,
      startedAt: state.startedAt,
      status: {
        state: state.status,
        message: '파이프라인을 시작했습니다.',
        step: state.currentStep,
        artifacts: [],
        gitDiff: '-',
        reviewStatus: '-'
      }
    });
  } catch (error) {
    handleError(res, error);
  }
});

app.post('/api/pipeline/reset', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.body.projectDir);
    const jobId = validateJobId(req.body.jobId);
    const key = pipelineKey(projectDir, jobId);
    pipelineStates.delete(key);
    res.json({
      ok: true,
      jobKey: key,
      status: {
        state: 'idle',
        message: '선택한 작업의 파이프라인 상태를 초기화했습니다.',
        step: null,
        artifacts: [],
        gitDiff: '-',
        reviewStatus: '-'
      }
    });
  } catch (error) {
    handleError(res, error);
  }
});

app.get('/api/pipeline/status', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.query.projectDir);
    const jobId = validateJobId(req.query.jobId);
    const key = pipelineKey(projectDir, jobId);
    const state = pipelineStates.get(key);
    if (state) {
      await applyArtifactProgress(state);
      await refreshApprovalState(state);
      markTimedOutRunningStep(state);
      await refreshPipelineArtifacts(state);
      if (state.status !== 'running') {
        await updateReviewSummary(projectDir, jobId, state);
      }
      res.json(publicPipelineState(state));
      return;
    }

    res.json(publicIdlePipelineState(projectDir, jobId));
  } catch (error) {
    handleError(res, error);
  }
});

app.get('/api/tmux/windows', async (req, res) => {
  try {
    const result = await runFile('tmux', ['list-windows', '-t', SESSION, '-F', '#W']);
    const existing = result.ok
      ? result.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
      : [];
    const windows = [...ALLOWED_TMUX_WINDOWS].map((name) => ({
      name,
      available: existing.includes(name)
    }));
    res.json({ ok: true, windows });
  } catch (error) {
    handleError(res, error);
  }
});

app.get('/api/tmux/output', async (req, res) => {
  try {
    const windowName = validateTmuxWindow(req.query.window);
    const result = await runFile('tmux', ['capture-pane', '-p', '-S', '-200', '-t', `${SESSION}:${windowName}`], {
      timeout: 10000,
      maxBuffer: 512 * 1024
    });
    res.json({
      ok: result.ok,
      window: windowName,
      output: redactedOutput(result.stdout || result.stderr || result.message)
    });
  } catch (error) {
    handleError(res, error);
  }
});

for (const [endpoint, keys] of [
  ['/api/tmux/approve-once', ['1', 'Enter']],
  ['/api/tmux/approve-session', ['2', 'Enter']],
  ['/api/tmux/reject', ['3', 'Enter']],
  ['/api/tmux/interrupt', ['C-c']]
]) {
  app.post(endpoint, async (req, res) => {
    try {
      const windowName = validateTmuxWindow(req.body.window);
      const result = await sendKeysToWindow(windowName, keys);
      res.json({
        ok: result.ok,
        window: windowName,
        output: redactedOutput(`${result.stdout || ''}${result.stderr || ''}${result.message || ''}`)
      });
    } catch (error) {
      handleError(res, error);
    }
  });
}

app.get('/api/service/status', async (req, res) => {
  try {
    res.json({
      ok: true,
      aiTeamRunning: await tmuxSessionRunning(SESSION),
      gui: {
        host: HOST,
        port: PORT,
        pid: process.pid,
        uptimeSeconds: Math.round(process.uptime())
      }
    });
  } catch (error) {
    handleError(res, error);
  }
});

app.post('/api/service/restart-ai-team', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.body.projectDir);
    if (await tmuxSessionRunning(SESSION)) {
      const stopped = await runFile('tmux', ['kill-session', '-t', SESSION], { timeout: 10000 });
      if (!stopped.ok) {
        res.status(500).json(cleanOutput(stopped));
        return;
      }
    }
    const started = await runFile(path.join(SCRIPTS_DIR, 'start-ai-team.sh'), [projectDir], {
      cwd: ROOT_DIR,
      env: { ...process.env, TERM: process.env.TERM || 'xterm-256color' },
      timeout: 30000
    });
    res.json(cleanOutput(started));
  } catch (error) {
    handleError(res, error);
  }
});

app.post('/api/service/restart-gui', async (req, res) => {
  try {
    const restartSession = `ai-gui-restart-${Date.now()}`;
    const serverPath = path.join(__dirname, 'server.js');
    const command = `sleep 1; exec node ${shellQuote(serverPath)}`;
    const started = await runFile('tmux', ['new-session', '-d', '-s', restartSession, '-c', ROOT_DIR, command], {
      timeout: 10000
    });
    if (!started.ok) {
      res.status(500).json(cleanOutput(started));
      return;
    }
    res.json({ ok: true, output: 'GUI 서버 재시작을 예약했습니다.' });
    setTimeout(() => process.exit(0), 250);
  } catch (error) {
    handleError(res, error);
  }
});

for (const [endpoint, role] of [
  ['/api/send/gemini', 'gemini'],
  ['/api/send/claude-architect', 'claude-architect'],
  ['/api/send/codex', 'codex'],
  ['/api/send/claude-reviewer', 'claude-reviewer']
]) {
  app.post(endpoint, async (req, res) => {
    try {
      const projectDir = await resolveProjectDir(req.body.projectDir);
      const jobId = validateJobId(req.body.jobId);
      const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
      const result = await sendToWindow(role, projectDir, jobId, inputKo);
      res.json(cleanOutput(result));
    } catch (error) {
      handleError(res, error);
    }
  });
}

app.get('/api/git/status', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.query.projectDir);
    const result = await runFile('git', ['status', '--short'], { cwd: projectDir });
    res.json(cleanOutput(result));
  } catch (error) {
    handleError(res, error);
  }
});

app.get('/api/git/diff', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.query.projectDir);
    const result = await runFile('git', ['diff', '--', '.'], { cwd: projectDir, timeout: 30000, maxBuffer: 5 * 1024 * 1024 });
    res.json(cleanOutput(result));
  } catch (error) {
    handleError(res, error);
  }
});

app.get('/api/artifacts', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.query.projectDir);
    const jobId = validateJobId(req.query.jobId);
    resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId));
    const files = await listArtifacts(projectDir, jobId);
    res.json({ ok: true, files });
  } catch (error) {
    handleError(res, error);
  }
});

app.get('/api/artifact', async (req, res) => {
  try {
    const projectDir = await resolveProjectDir(req.query.projectDir);
    const artifactPath = req.query.path;
    const absolute = resolveJobArtifact(projectDir, artifactPath);
    const name = path.basename(absolute);
    if (!ARTIFACT_NAMES.has(name)) {
      throw new Error('허용된 산출물 파일만 읽을 수 있습니다.');
    }
    const stat = await fs.stat(absolute);
    if (!stat.isFile() || stat.size > 1024 * 1024) {
      throw new Error('읽을 수 없는 파일입니다.');
    }
    const content = await fs.readFile(absolute, 'utf8');
    res.json({ ok: true, path: artifactPath, content });
  } catch (error) {
    handleError(res, error);
  }
});

app.use('/api', (req, res) => {
  res.status(404).json({ ok: false, error: 'Unknown API endpoint' });
});

app.use((error, req, res, next) => {
  if (req.path && req.path.startsWith('/api/')) {
    res.status(error.status || 500).json({ ok: false, error: error.message || '요청을 처리할 수 없습니다.' });
    return;
  }
  next(error);
});

app.listen(PORT, HOST, () => {
  console.log(`AI Team GUI running at http://${HOST}:${PORT}`);
});

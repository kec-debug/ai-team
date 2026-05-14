const express = require('express');
const fs = require('fs/promises');
const path = require('path');
const { execFile, spawn } = require('child_process');

const app = express();
const HOST = process.env.HOST || '127.0.0.1';
const PORT = Number(process.env.PORT || 3100);
const SESSION = 'ai-team';
const GUI_SESSION = 'ai-gui';
const ROOT_DIR = path.resolve(__dirname, '..');
const SCRIPTS_DIR = path.join(ROOT_DIR, 'scripts');
const WEB_DIR = path.join(ROOT_DIR, 'web');
const GUI_RESTART_LOG = '/tmp/ai-team-gui-restart.log';
const SAFE_WINDOWS = {
  'claude-plan': 'claude',
  'codex-implement': 'codex',
  'claude-review': 'claude',
  'codex-review-fix': 'codex',
  'claude-re-review': 'claude',
  claude: 'claude',
  codex: 'codex'
};
const ALLOWED_TMUX_WINDOWS = new Set([
  'claude',
  'codex',
  'git-shell'
]);
const AI_TMUX_WINDOWS = new Set([
  'claude',
  'codex'
]);
const TMUX_WINDOW_LABELS = {
  claude: 'Claude - planning, requirements, review',
  codex: 'Codex - implementation, tests, patch summary',
  'git-shell': 'Manual Shell - git status, git diff, tests, human commit/PR commands'
};
const PIPELINE_STEP_TIMEOUT_MS = Number(process.env.AI_TEAM_PIPELINE_STEP_TIMEOUT_MS || 15 * 60 * 1000);
const PIPELINE_POLL_MS = Number(process.env.AI_TEAM_PIPELINE_POLL_MS || 5000);
const MANUAL_REQUIRED_MESSAGE = 'AI CLI 창에서 승인 대기 중일 수 있습니다. 아래 승인 버튼을 누르거나 tmux 출력을 확인하세요.';
const ISSUE_RECOMMENDATIONS = {
  blocked: 'AI가 작업을 차단했습니다. 작업 범위를 줄이거나 금지 항목을 별도 작업으로 분리한 뒤 다시 실행하세요.',
  approval_required: 'AI CLI가 승인 대기 중일 수 있습니다. 승인/세션 승인/거절/중단 버튼을 사용하세요.',
  failed: '실행 오류가 감지되었습니다. 로그를 확인하고 인증/명령/서버 상태를 점검하세요.',
  manual_review_required: MANUAL_REQUIRED_MESSAGE
};
const ISSUE_PATTERNS = [
  {
    type: 'blocked',
    patterns: [
      /진행할 수 없습니다/i,
      /규정 위반/i,
      /요구사항을 다시 작성/i,
      /정책상|정책 위반|안전 정책/i,
      /policy violation|violates policy|disallowed|cannot comply|can't comply|cannot assist/i
    ]
  },
  {
    type: 'approval_required',
    patterns: [
      /allow execution|allow edit|do you want to proceed|would you like to continue|allow for this session|no, suggest changes|enter your response/i
    ]
  },
  {
    type: 'failed',
    patterns: [
      /error:|fatal:|exception|traceback|failed|failure/i,
      /command not found|permission denied|authentication failed|not authenticated/i,
      /오류|에러|실패|예외|권한.*거부|인증.*실패/i
    ]
  },
  {
    type: 'manual_review_required',
    patterns: [
      /manual intervention|required manual|수동.*필요|직접.*확인|사람.*확인/i
    ]
  }
];
const pipelineStates = new Map();
const PIPELINE_STAGES = [
  { id: 'claude-plan', state: 'claude_planning', label: 'Claude 계획 생성', role: 'claude-plan', window: 'claude', artifacts: ['plan.md', 'codex-task.md'] },
  { id: 'codex-implement', state: 'codex_implementing', label: 'Codex 구현 실행', role: 'codex-implement', window: 'codex', artifacts: ['patch.md'] },
  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] },
  { id: 'codex-review-fix', state: 'codex_fixing_review', label: 'Codex 리뷰 반영 실행', role: 'codex-review-fix', window: 'codex', artifacts: ['status.md'] },
  { id: 'claude-re-review', state: 'claude_re_reviewing', label: 'Claude 재리뷰 실행', role: 'claude-re-review', window: 'claude', artifacts: ['review.md'] }
];
const ACTIVE_PIPELINE_STATES = new Set([
  'claude_planning',
  'codex_implementing',
  'claude_reviewing',
  'codex_fixing_review',
  'claude_re_reviewing',
  'approval_required'
]);
const FINAL_PIPELINE_STATES = new Set([
  'succeeded',
  'failed',
  'blocked',
  'manual_review_required',
  'review_approved',
  'review_changes_requested',
  'manual_final_approval_required',
  'idle'
]);
const ARTIFACT_PRIORITY = [
  'request.ko.md',
  'plan.md',
  'codex-task.md',
  'patch.md',
  'review.md',
  'status.md'
];
const ARTIFACT_NAMES = new Set([
  'README.md',
  'request.ko.md',
  'input.ko.md',
  'input.en.md',
  'plan.en.md',
  'plan.md',
  'codex-task.md',
  'gemini-plan.en.md',
  'architecture.md',
  'claude-design-review.en.md',
  'codex-prompt.en.md',
  'patch.md',
  'codex-summary.en.md',
  'review.md',
  'claude-pr-review.en.md',
  'status.md',
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

function validateAiTmuxWindow(windowName) {
  const safeWindow = validateTmuxWindow(windowName);
  if (!AI_TMUX_WINDOWS.has(safeWindow)) {
    throw new Error('승인/거절 제어는 Claude 또는 Codex AI 창에서만 사용할 수 있습니다.');
  }
  return safeWindow;
}

function stageById(stageId) {
  return PIPELINE_STAGES.find((stage) => stage.id === stageId) || null;
}

function currentTargetWindow(state) {
  const stage = stageById(state.currentStep);
  return stage ? stage.window : null;
}

function stageByState(status) {
  return PIPELINE_STAGES.find((stage) => stage.state === status) || null;
}

function stageForGate(status, currentStep) {
  return stageById(currentStep) || stageByState(status) || PIPELINE_STAGES[0];
}

function nextStageGate(state) {
  if (!state) {
    return PIPELINE_STAGES[0];
  }
  if (state.status === 'succeeded' || state.status === 'review_approved' || state.status === 'manual_final_approval_required') {
    return null;
  }
  if (state.status === 'review_changes_requested') {
    return stageById('codex-review-fix');
  }
  return stageForGate(state.status, state.currentStep);
}

function artifactPath(projectDir, jobId, name) {
  return path.join(projectDir, 'docs', 'ai', 'jobs', jobId, name);
}

async function artifactStat(projectDir, jobId, name) {
  const stat = await fs.stat(artifactPath(projectDir, jobId, name)).catch(() => null);
  return stat && stat.isFile() && stat.size > 0 ? stat : null;
}

async function artifactExists(projectDir, jobId, name, afterIso = null) {
  const stat = await artifactStat(projectDir, jobId, name);
  if (!stat) {
    return false;
  }
  if (!afterIso) {
    return true;
  }
  const after = Date.parse(afterIso);
  return Number.isNaN(after) ? true : stat.mtimeMs >= after;
}

async function artifactStatus(projectDir, jobId, names, afterIso = null) {
  const files = [];
  for (const name of names) {
    const stat = await artifactStat(projectDir, jobId, name);
    const exists = stat ? await artifactExists(projectDir, jobId, name, afterIso) : false;
    files.push({ name, exists, modifiedAt: stat ? stat.mtime.toISOString() : null });
  }
  return files;
}

async function allArtifactsExist(projectDir, jobId, names, afterIso = null) {
  const files = await artifactStatus(projectDir, jobId, names, afterIso);
  return {
    ok: files.every((file) => file.exists),
    files,
    missing: files.filter((file) => !file.exists).map((file) => file.name)
  };
}

async function buildStageRequirements(projectDir, jobId, stage) {
  if (!stage) {
    return {
      stage: null,
      label: null,
      files: [],
      missing: [],
      nextStageAllowed: true,
      guidance: ''
    };
  }
  const requirements = await allArtifactsExist(projectDir, jobId, stage.artifacts);
  return {
    stage: stage.id,
    label: stage.label,
    files: requirements.files,
    missing: requirements.missing,
    nextStageAllowed: requirements.ok,
    guidance: requirements.ok
      ? '다음 단계를 실행할 수 있습니다.'
      : `필수 산출물이 아직 생성되지 않았습니다: ${requirements.missing.join(', ')}`
  };
}

async function publicIdlePipelineState(projectDir = null, jobId = null) {
  const now = new Date().toISOString();
  const artifacts = projectDir && jobId ? await listArtifacts(projectDir, jobId) : [];
  const requirements = projectDir && jobId
    ? await buildStageRequirements(projectDir, jobId, PIPELINE_STAGES[0])
    : await buildStageRequirements(null, null, null);
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
      detectedIssue: null,
      artifacts,
      gitDiff: '-',
      reviewStatus: '-',
      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.',
      requirements
    },
    artifacts,
    summary: {
      createdArtifacts: artifacts.map((artifact) => artifact.name),
      gitDiff: { hasChanges: false, saved: false, path: null, changedFiles: [] },
      review: { status: 'not_started', file: null, decision: null }
    }
  };
}

async function publicPipelineState(state) {
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
  const detectedIssue = state.detectedIssue || null;
  const requirements = await buildStageRequirements(state.projectDir, state.jobId, nextStageGate(state));

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
      waitingApproval: state.status === 'approval_required' || (detectedIssue && detectedIssue.type === 'approval_required'),
      detectedIssue,
      artifacts: state.artifacts,
      gitDiff: gitDiffText,
      reviewStatus,
      nextAction: nextRecommendedAction(state, reviewStatus),
      requirements
    },
    steps: state.steps,
    artifacts: state.artifacts,
    summary: state.summary
  };
}

function pipelineMessage(status) {
  if (status === 'claude_planning') {
    return 'Claude가 계획과 Codex 작업 지시문을 작성하는 단계입니다.';
  }
  if (status === 'codex_implementing') {
    return 'Codex가 구현, 테스트, 패치 요약을 진행하는 단계입니다.';
  }
  if (status === 'claude_reviewing') {
    return 'Claude가 현재 diff와 패치 요약을 리뷰하는 단계입니다.';
  }
  if (status === 'codex_fixing_review') {
    return 'Codex가 Claude 리뷰의 수정 요청만 반영하는 단계입니다.';
  }
  if (status === 'claude_re_reviewing') {
    return 'Claude가 수정 반영 후 diff를 다시 리뷰하는 단계입니다.';
  }
  if (status === 'review_approved' || status === 'manual_final_approval_required') {
    return 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.';
  }
  if (status === 'review_changes_requested') {
    return 'Claude가 수정 요청을 남겼습니다. Codex가 리뷰 내용을 반영해야 합니다.';
  }
  if (status === 'succeeded') {
    return '파이프라인이 완료되었습니다.';
  }
  if (status === 'failed') {
    return '파이프라인 실행에 실패했습니다.';
  }
  if (status === 'blocked') {
    return ISSUE_RECOMMENDATIONS.blocked;
  }
  if (status === 'approval_required') {
    return MANUAL_REQUIRED_MESSAGE;
  }
  if (status === 'manual_review_required') {
    return MANUAL_REQUIRED_MESSAGE;
  }
  return '아직 실행되지 않았습니다.';
}

function nextRecommendedAction(state, reviewStatus) {
  if (state.status === 'review_approved' || state.status === 'manual_final_approval_required' || state.status === 'succeeded') {
    return reviewStatus && reviewStatus !== '-'
      ? 'Claude 리뷰 결과를 확인한 뒤 사람이 직접 commit, push, PR 생성 여부를 결정하세요.'
      : '산출물과 git diff를 확인한 뒤 사람이 직접 다음 작업을 결정하세요.';
  }
  if (state.status === 'review_changes_requested') {
    return 'Codex 리뷰 반영 실행을 눌러 Claude가 요청한 수정만 반영하세요.';
  }
  if (state.status === 'manual_review_required' || state.status === 'approval_required') {
    return 'tmux 출력을 확인하고 필요한 경우 승인 / 계속 진행, 세션 승인, 거절, 중단 중 하나를 선택하세요.';
  }
  if (state.status === 'blocked') {
    return ISSUE_RECOMMENDATIONS.blocked;
  }
  if (state.status === 'failed') {
    return '오류 메시지와 tmux 출력을 확인한 뒤 상태 초기화 또는 수동 복구를 진행하세요.';
  }
  if (ACTIVE_PIPELINE_STATES.has(state.status)) {
    return '현재 단계의 tmux 출력을 보면서 진행 상황을 확인하세요.';
  }
  return 'Claude → Codex → Claude 전체 실행을 시작하세요.';
}

function createPipelineState(projectDir, jobId) {
  const now = new Date().toISOString();
  const key = pipelineKey(projectDir, jobId);
  return {
    jobKey: key,
    projectDir,
    jobId,
    status: 'claude_planning',
    currentStep: 'queued',
    startedAt: now,
    finishedAt: null,
    updatedAt: now,
    error: null,
    detectedIssue: null,
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
  if (['succeeded', 'failed', 'blocked', 'manual_review_required', 'approval_required'].includes(status)) {
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
    .sort((a, b) => {
      const aPriority = ARTIFACT_PRIORITY.indexOf(a.name);
      const bPriority = ARTIFACT_PRIORITY.indexOf(b.name);
      if (aPriority !== -1 || bPriority !== -1) {
        return (aPriority === -1 ? 999 : aPriority) - (bPriority === -1 ? 999 : bPriority);
      }
      return a.name.localeCompare(b.name);
    });
}

async function refreshPipelineArtifacts(state) {
  state.artifacts = await listArtifacts(state.projectDir, state.jobId);
  state.summary.createdArtifacts = state.artifacts.map((artifact) => artifact.name);
  state.updatedAt = new Date().toISOString();
}

async function findFirstExistingArtifact(projectDir, jobId, names) {
  for (const name of names) {
    if (await artifactExists(projectDir, jobId, name)) {
      return { name, path: artifactPath(projectDir, jobId, name) };
    }
  }
  return null;
}

async function waitForArtifacts(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
  const started = Date.now();
  const afterIso = state && state.currentStep
    ? state.steps.find((step) => step.id === state.currentStep)?.startedAt || null
    : null;
  while (Date.now() - started < timeoutMs) {
    if (state && !ACTIVE_PIPELINE_STATES.has(state.status)) {
      return null;
    }
    const requirements = await allArtifactsExist(projectDir, jobId, names, afterIso);
    if (requirements.ok) {
      return requirements.files;
    }
    await new Promise((resolve) => setTimeout(resolve, PIPELINE_POLL_MS));
  }
  return null;
}

function markManualRequired(state, stepId, label) {
  state.status = 'manual_review_required';
  state.finishedAt = new Date().toISOString();
  state.updatedAt = state.finishedAt;
  state.error = MANUAL_REQUIRED_MESSAGE;
  state.detectedIssue = state.detectedIssue || {
    type: 'manual_review_required',
    window: currentTargetWindow(state),
    summary: MANUAL_REQUIRED_MESSAGE,
    recommendation: ISSUE_RECOMMENDATIONS.manual_review_required
  };
  setStep(state, stepId, label, 'manual_review_required', MANUAL_REQUIRED_MESSAGE);
}

function markTimedOutRunningStep(state) {
  if (!ACTIVE_PIPELINE_STATES.has(state.status) || !state.currentStep) {
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

function summarizeIssue(output, type) {
  if (type === 'approval_required') {
    const block = extractApprovalBlock(output);
    return block ? block.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)[0]?.slice(0, 220) || ISSUE_RECOMMENDATIONS[type] : ISSUE_RECOMMENDATIONS[type];
  }
  const lines = String(output || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const matcher = ISSUE_PATTERNS.find((item) => item.type === type);
  if (matcher) {
    const matched = lines.find((line) => matcher.patterns.some((pattern) => pattern.test(line)));
    if (matched) {
      return matched.slice(0, 220);
    }
  }
  return lines.slice(-3).join(' ').slice(0, 220) || ISSUE_RECOMMENDATIONS[type] || '최근 tmux 출력에서 확인이 필요한 상태를 감지했습니다.';
}

function isLikelyCodeOrSearchLine(line) {
  return /^\s*[+-]/.test(line)
    || /\bconst\s+|\bfunction\s+|=>|stageWindows|pipelineStates|server\.js|Search\s+/i.test(line)
    || /['"]approval_required['"]|['"]manual_review_required['"]/i.test(line)
    || /^\s*(web\/|app\/|docs\/|projects\/).+:\d+[:\s]/.test(line)
    || /^\s*```/.test(line);
}

function stripCodeLikeApprovalLines(output) {
  const lines = String(output || '').split(/\r?\n/);
  let inCodeBlock = false;
  const kept = [];
  for (const line of lines) {
    if (/^\s*```/.test(line)) {
      inCodeBlock = !inCodeBlock;
      continue;
    }
    if (inCodeBlock || isLikelyCodeOrSearchLine(line)) {
      continue;
    }
    kept.push(line);
  }
  return kept.join('\n');
}

function hasApprovalOptions(block) {
  return /(?:^|\n)\s*(?:1[.)]|2[.)]|3[.)]).*(?:allow|approve|session|reject|승인|세션|거절|continue)/i.test(block);
}

function hasCommandOrEditSummary(block) {
  return /(?:command|execute|run|edit|file|patch|modify|명령|실행|수정|편집|파일)\s*[:：]/i.test(block)
    || /\b(npm|node|python3?|git|mkdir|cat|chmod|cp|mv|rm|sudo|curl|gh)\b/i.test(block)
    || /[\w./-]+\.(?:js|css|html|md|json|py|ts|tsx|jsx|yml|yaml|sh)/i.test(block);
}

function findStrictApprovalPromptBlock(output) {
  const cleaned = stripCodeLikeApprovalLines(output);
  const lines = cleaned.split(/\r?\n/);
  const strongPattern = /allow execution|allow edit|do you want to proceed|would you like to continue|allow for this session|no, suggest changes|enter your response/i;
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    if (!strongPattern.test(lines[i])) {
      continue;
    }
    const block = lines.slice(Math.max(0, i - 8), Math.min(lines.length, i + 10)).join('\n').trim();
    if (hasApprovalOptions(block) || hasCommandOrEditSummary(block)) {
      return block;
    }
  }
  return '';
}

function detectIssueFromOutput(output, windowName) {
  const text = String(output || '');
  for (const category of ISSUE_PATTERNS) {
    if (category.type === 'approval_required') {
      const block = findStrictApprovalPromptBlock(text);
      if (block) {
        return {
          type: category.type,
          window: windowName,
          summary: summarizeIssue(block, category.type),
          recommendation: ISSUE_RECOMMENDATIONS[category.type]
        };
      }
      continue;
    }
    if (category.patterns.some((pattern) => pattern.test(text))) {
      return {
        type: category.type,
        window: windowName,
        summary: summarizeIssue(text, category.type),
        recommendation: ISSUE_RECOMMENDATIONS[category.type]
      };
    }
  }
  return null;
}

async function captureRecentTmuxOutput(windowName, lines = 120) {
  const safeWindow = validateTmuxWindow(windowName);
  const result = await runFile('tmux', ['capture-pane', '-p', '-S', `-${lines}`, '-t', `${SESSION}:${safeWindow}`], {
    timeout: 10000,
    maxBuffer: 256 * 1024
  });
  return result.ok ? redactedOutput(result.stdout) : '';
}

function approvalTypeFromBlock(block) {
  if (/edit|patch|modify|write|수정|편집|파일/i.test(block)) {
    return 'file_edit';
  }
  if (/command|execute|run|명령|실행/i.test(block)) {
    return 'command_execution';
  }
  return 'unknown';
}

function extractCommandOrTarget(block) {
  const lines = String(block || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const commandLine = lines.find((line) => /^\$|^>|^`[^`]+`$|^(npm|node|python|python3|git|mkdir|cat|chmod|cp|mv|rm|sudo|curl|gh)\b/i.test(line));
  if (commandLine) {
    return commandLine.replace(/^[$>]\s*/, '').replace(/^`|`$/g, '').slice(0, 260);
  }
  const fileLine = lines.find((line) => /(?:^|\s)([\w./-]+\.(?:js|css|html|md|json|py|ts|tsx|jsx|yml|yaml|sh))(?:\s|$)/i.test(line));
  return fileLine ? fileLine.slice(0, 260) : '';
}

function classifyApprovalRisk(block, commandOrTarget) {
  const text = `${block || ''}\n${commandOrTarget || ''}`;
  if (/rm\s+-rf|sudo\b|curl\b.*\|\s*(bash|sh)|git\s+push|gh\s+pr\s+merge|deploy|deployment|kubectl|terraform|\.env|secret|token|api\s*key|auth\/|payment\/|billing\/|migrations?\/|production|prod\b/i.test(text)) {
    return {
      risk: 'high',
      recommendation: '거절 권장',
      canApproveOnce: false,
      canApproveSession: false,
      warning: '승인하지 마세요. 거절 또는 중단하세요.'
    };
  }
  if (/npm\s+install|chmod\b|\bcp\b|\bmv\b/i.test(text) || /(?:^|\s)(?!docs\/ai\/jobs\/)[\w./-]+\.(?:js|css|html|py|ts|tsx|jsx|json|yml|yaml|sh)/i.test(text)) {
    return {
      risk: 'medium',
      recommendation: '직접 확인 필요',
      canApproveOnce: true,
      canApproveSession: false,
      warning: '명령과 수정 대상을 tmux 출력에서 확인한 뒤 1회 승인만 고려하세요.'
    };
  }
  if (/mkdir\s+-p\s+docs\/ai\/jobs\/|docs\/ai\/jobs\/[\w._-]+|git\s+(status|diff)\b|node\s+--check\b|python3?\s+-m\s+(py_compile|compileall)\b|cat\s+docs\/ai\/jobs\//i.test(text)) {
    return {
      risk: 'low',
      recommendation: '1회 승인 가능',
      canApproveOnce: true,
      canApproveSession: true,
      warning: '세션 승인은 같은 종류의 안전한 명령이 반복될 때만 사용하세요.'
    };
  }
  return {
    risk: 'unknown',
    recommendation: '직접 확인 필요',
    canApproveOnce: false,
    canApproveSession: false,
    warning: '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.'
  };
}

function extractApprovalBlock(output) {
  return findStrictApprovalPromptBlock(output);
}

function cleanWorkingDirectory(block) {
  const match = String(block || '').match(/(?:cwd|working directory|작업 디렉터리)\s*[:=]\s*([^\n]+)/i);
  return match ? match[1].trim().slice(0, 260) : '-';
}

async function buildApprovalContext(windowName, step = null) {
  const safeWindow = validateAiTmuxWindow(windowName);
  const output = await captureRecentTmuxOutput(safeWindow, 180);
  const rawBlock = extractApprovalBlock(output);
  if (!rawBlock) {
    return null;
  }
  const commandOrTarget = extractCommandOrTarget(rawBlock);
  const risk = classifyApprovalRisk(rawBlock, commandOrTarget);
  return {
    window: safeWindow,
    step,
    type: approvalTypeFromBlock(rawBlock),
    commandOrTarget: commandOrTarget || '확인 불가',
    workingDirectory: cleanWorkingDirectory(rawBlock),
    rawBlock,
    ...risk,
    summary: `${safeWindow === 'codex' ? 'Codex' : 'Claude'} 창에서 명령 실행 승인 요청이 감지되었습니다.`
  };
}

async function refreshDetectedIssue(state) {
  if (!state || !ACTIVE_PIPELINE_STATES.has(state.status)) {
    return;
  }
  const targetWindow = currentTargetWindow(state);
  if (!targetWindow) {
    return;
  }
  const output = await captureRecentTmuxOutput(targetWindow, 120);
  const issue = detectIssueFromOutput(output, targetWindow);
  if (!issue) {
    return;
  }
  if (issue.type === 'approval_required') {
    issue.approvalContext = await buildApprovalContext(targetWindow, state.currentStep).catch(() => null);
    if (!issue.approvalContext) {
      return;
    }
    issue.summary = issue.approvalContext.summary;
  }

  state.detectedIssue = issue;
  state.error = issue.recommendation;
  state.updatedAt = new Date().toISOString();

  if (issue.type === 'blocked') {
    state.status = 'blocked';
    state.finishedAt = state.updatedAt;
    setStep(state, state.currentStep, stageById(state.currentStep)?.label || state.currentStep, 'blocked', issue.summary);
  } else if (issue.type === 'failed') {
    state.status = 'failed';
    state.finishedAt = state.updatedAt;
    setStep(state, state.currentStep, stageById(state.currentStep)?.label || state.currentStep, 'failed', issue.summary);
  } else if (issue.type === 'approval_required') {
    state.status = 'approval_required';
  } else if (issue.type === 'manual_review_required') {
    markManualRequired(state, state.currentStep, stageById(state.currentStep)?.label || state.currentStep);
  }
}

async function applyArtifactProgress(state) {
  if (!state || !ACTIVE_PIPELINE_STATES.has(state.status)) {
    return;
  }

  const current = stageById(state.currentStep);
  if (current) {
    const step = state.steps.find((item) => item.id === current.id);
    const requirements = await allArtifactsExist(state.projectDir, state.jobId, current.artifacts, step?.startedAt || null);
    if (requirements.ok) {
      state.status = current.state;
      state.error = null;
      state.detectedIssue = null;
      setStep(state, current.id, current.label, 'succeeded', requirements.files.map((file) => file.name).join(', '));
      if (current.id === 'codex-review-fix') {
        state.status = 'review_changes_requested';
        state.currentStep = null;
        state.error = 'Codex가 리뷰 반영을 완료했습니다. Claude 재리뷰를 실행하세요.';
      }
      if (current.id === 'claude-review' || current.id === 'claude-re-review') {
        await updateReviewSummary(state.projectDir, state.jobId, state);
        applyReviewDecision(state);
      }
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
  const artifact = await findFirstExistingArtifact(projectDir, jobId, ['review.md', 'claude-pr-review.en.md']);
  if (!artifact) {
    state.summary.review = { status: 'not_found', file: null, decision: null };
    return;
  }
  const content = await fs.readFile(artifact.path, 'utf8').catch(() => '');
  const decision = detectReviewDecision(content);
  const decisionLine = content.split(/\r?\n/).find((line) => /decision|verdict|approve|request[_ -]?changes|block|승인|수정\s*요청|차단|보류/i.test(line));
  state.summary.review = {
    status: 'available',
    file: artifact.name,
    decision,
    decisionLine: decisionLine ? decisionLine.trim() : null
  };
}

function detectReviewDecision(content) {
  const text = String(content || '');
  if (/\bBLOCK\b|차단|보류/i.test(text)) {
    return 'BLOCK';
  }
  if (/\bREQUEST[_ -]?CHANGES\b|수정\s*요청/i.test(text)) {
    return 'REQUEST_CHANGES';
  }
  if (/\bAPPROVE\b|\bAPPROVED\b|승인/i.test(text)) {
    return 'APPROVE';
  }
  return 'UNKNOWN';
}

function applyReviewDecision(state) {
  const decision = state.summary.review.decision;
  const now = new Date().toISOString();
  if (decision === 'APPROVE') {
    state.status = 'manual_final_approval_required';
    state.currentStep = null;
    state.finishedAt = now;
    state.error = 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.';
    return;
  }
  if (decision === 'REQUEST_CHANGES') {
    state.status = 'review_changes_requested';
    state.currentStep = null;
    state.finishedAt = now;
    state.error = 'Claude가 수정 요청을 남겼습니다. Codex가 리뷰 내용을 반영해야 합니다.';
    return;
  }
  if (decision === 'BLOCK') {
    state.status = 'blocked';
    state.currentStep = null;
    state.finishedAt = now;
    state.error = 'Claude가 작업을 차단했습니다. 요청 범위나 안전 조건을 수정해야 합니다.';
    return;
  }
  state.status = 'manual_review_required';
  state.currentStep = null;
  state.finishedAt = now;
  state.error = 'Claude 리뷰 결정을 확인할 수 없습니다. review.md에서 APPROVE, REQUEST_CHANGES, BLOCK 중 하나를 확인하세요.';
}

async function runPipeline(state, inputKo) {
  const { projectDir, jobId } = state;
  const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
  try {
    setStep(state, 'create-job', '작업 폴더 생성', 'running');
    await fs.mkdir(jobDir, { recursive: true });
    await appendPipelineLog(projectDir, jobId, 'create-job', `Ensured job directory: ${jobDir}`);
    setStep(state, 'create-job', '작업 폴더 생성', 'succeeded', jobDir);

    setStep(state, 'save-input', 'request.ko.md 저장', 'running');
    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'request.ko.md'));
    await fs.writeFile(inputPath, inputKo, 'utf8');
    await appendPipelineLog(projectDir, jobId, 'save-input', `Saved: ${inputPath}`);
    setStep(state, 'save-input', 'request.ko.md 저장', 'succeeded', inputPath);
    await refreshPipelineArtifacts(state);

    for (const step of PIPELINE_STAGES.slice(0, 2)) {
      state.status = step.state;
      state.error = null;
      setStep(state, step.id, step.label, 'running');
      const sent = await sendToWindow(step.role, projectDir, jobId, inputKo);
      await appendPipelineLog(projectDir, jobId, step.id, `${sent.stdout || ''}${sent.stderr || ''}${sent.message || ''}`);
      if (!sent.ok) {
        throw new Error(`${step.label} 실패: ${sent.message || sent.stderr || 'tmux 전송 실패'}`);
      }
      const artifacts = await waitForArtifacts(projectDir, jobId, step.artifacts, state);
      if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
        return;
      }
      if (!artifacts) {
        markManualRequired(state, step.id, step.label);
        await refreshPipelineArtifacts(state);
        return;
      }
      state.status = step.state;
      state.error = null;
      state.detectedIssue = null;
      setStep(state, step.id, step.label, 'succeeded', artifacts.map((artifact) => artifact.name).join(', '));
      await refreshPipelineArtifacts(state);

      if (step.id === 'codex-implement') {
        const denied = (await changedFiles(projectDir)).filter(isDeniedSafetyPath);
        if (denied.length > 0) {
          state.status = 'blocked';
          state.finishedAt = new Date().toISOString();
          state.error = `안전 차단 경로 변경 감지: ${denied.join(', ')}`;
          setStep(state, 'safety-check', '안전 경로 확인', 'blocked', state.error);
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

    const reviewerStep = PIPELINE_STAGES[2];
    state.status = reviewerStep.state;
    state.error = null;
    setStep(state, reviewerStep.id, reviewerStep.label, 'running');
    const reviewed = await sendToWindow(reviewerStep.role, projectDir, jobId, inputKo);
    await appendPipelineLog(projectDir, jobId, 'claude-review', `${reviewed.stdout || ''}${reviewed.stderr || ''}${reviewed.message || ''}`);
    if (!reviewed.ok) {
      throw new Error(`Claude 리뷰 전송 실패: ${reviewed.message || reviewed.stderr || 'tmux 전송 실패'}`);
    }
    const reviewArtifacts = await waitForArtifacts(projectDir, jobId, reviewerStep.artifacts, state);
    if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
      return;
    }
    if (!reviewArtifacts) {
      markManualRequired(state, reviewerStep.id, reviewerStep.label);
      await updateReviewSummary(projectDir, jobId, state);
      await refreshPipelineArtifacts(state);
      return;
    }
    state.status = reviewerStep.state;
    state.error = null;
    state.detectedIssue = null;
    setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifacts.map((artifact) => artifact.name).join(', '));
    await updateReviewSummary(projectDir, jobId, state);
    await refreshPipelineArtifacts(state);
    applyReviewDecision(state);
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

  if (role === 'claude-plan') {
    return [
      'Use prompts/claude.md.',
      common,
      '',
      `Read docs/ai/CLAUDE_CODEX_WORKFLOW.md and ${path.join(jobDir, 'request.ko.md')}.`,
      `Create the implementation plan in ${path.join(jobDir, 'plan.md')} and the Codex task in ${path.join(jobDir, 'codex-task.md')}.`,
      'Use the Claude planning output format from prompts/claude.md. Do not commit, push, merge, deploy, or touch secrets.',
      '',
      inputKo || `(Read from ${path.join(jobDir, 'request.ko.md')})`
    ].join('\n');
  }

  if (role === 'codex-implement') {
    return [
      'Use prompts/codex-implementer.md.',
      common,
      '',
      `Read ${path.join(jobDir, 'plan.md')} and ${path.join(jobDir, 'codex-task.md')}. Use ${path.join(jobDir, 'request.ko.md')} as scope context only.`,
      `Implement only the approved job scope, run applicable checks, and write ${path.join(jobDir, 'patch.md')}.`,
      'Do not commit, push, merge, deploy, or change secrets, .env, auth, payment, production infra, or database migrations.'
    ].join('\n');
  }

  if (role === 'claude-review') {
    return [
      'Use prompts/claude.md.',
      common,
      '',
      `Review the git diff saved at ${path.join(jobDir, 'local-diff.patch')} when present, ${path.join(jobDir, 'patch.md')}, and the approved request/plan.`,
      `Write the review into ${path.join(jobDir, 'review.md')} using the Claude review output format.`,
      'The review must include exactly one decision marker: APPROVE, REQUEST_CHANGES, or BLOCK.',
      'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
    ].join('\n');
  }

  if (role === 'codex-review-fix') {
    return [
      'Use prompts/codex-implementer.md.',
      common,
      '',
      `Read ${path.join(jobDir, 'patch.md')}, ${path.join(jobDir, 'review.md')}, and the current git diff.`,
      'Apply only the changes explicitly requested by Claude review. Do not expand scope.',
      `Update ${path.join(jobDir, 'patch.md')} and write ${path.join(jobDir, 'status.md')} with what changed and which checks ran.`,
      'Do not commit, push, merge, deploy, or change secrets, .env, auth, payment, production infra, or database migrations.'
    ].join('\n');
  }

  if (role === 'claude-re-review') {
    return [
      'Use prompts/claude.md.',
      common,
      '',
      `Re-review the updated git diff, ${path.join(jobDir, 'patch.md')}, ${path.join(jobDir, 'status.md')}, and the previous review in ${path.join(jobDir, 'review.md')}.`,
      `Update ${path.join(jobDir, 'review.md')} with the new review result.`,
      'The review must include exactly one decision marker: APPROVE, REQUEST_CHANGES, or BLOCK.',
      'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
    ].join('\n');
  }

  throw new Error('허용되지 않은 대상입니다.');
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
  const safeWindow = validateAiTmuxWindow(windowName);
  return runFile('tmux', ['send-keys', '-t', `${SESSION}:${safeWindow}`, ...keys]);
}

async function tmuxSessionRunning(sessionName) {
  const result = await runFile('tmux', ['has-session', '-t', sessionName]);
  return result.ok;
}

function shellQuote(value) {
  return `'${String(value).replace(/'/g, `'\\''`)}'`;
}

function buildGuiRestartScript() {
  const quotedLog = shellQuote(GUI_RESTART_LOG);
  const quotedWebDir = shellQuote(WEB_DIR);
  const quotedSession = shellQuote(GUI_SESSION);
  const npmCommand = `env HOST=0.0.0.0 PORT=3100 npm start >> ${quotedLog} 2>&1`;
  return [
    `LOG=${quotedLog}`,
    `echo "===== GUI restart requested: $(date -Is) =====" >> "$LOG"`,
    'sleep 1',
    `echo "[1] kill old tmux session ${GUI_SESSION}" >> "$LOG"`,
    `tmux kill-session -t ${quotedSession} >> "$LOG" 2>&1 || true`,
    'echo "[2] free port 3100" >> "$LOG"',
    'if command -v fuser >/dev/null 2>&1; then',
    '  fuser -k 3100/tcp >> "$LOG" 2>&1 || true',
    'elif command -v lsof >/dev/null 2>&1; then',
    '  pids="$(lsof -ti tcp:3100 2>>"$LOG" || true)"',
    '  if [ -n "$pids" ]; then kill $pids >> "$LOG" 2>&1 || true; fi',
    'else',
    '  echo "No fuser or lsof available; port cleanup skipped." >> "$LOG"',
    'fi',
    'sleep 1',
    `echo "[3] create tmux session ${GUI_SESSION}" >> "$LOG"`,
    `tmux new-session -d -s ${quotedSession} -c ${quotedWebDir} ${shellQuote(npmCommand)} >> "$LOG" 2>&1`,
    'status=$?',
    'echo "[4] tmux session creation result: $status" >> "$LOG"',
    'sleep 2',
    'echo "[5] port 3100 status" >> "$LOG"',
    '(command -v ss >/dev/null 2>&1 && ss -ltnp "sport = :3100" >> "$LOG" 2>&1) || true',
    'echo "===== GUI restart script finished: $(date -Is) =====" >> "$LOG"'
  ].join('\n');
}

function scheduleGuiRestart() {
  const child = spawn('sh', ['-lc', buildGuiRestartScript()], {
    detached: true,
    stdio: 'ignore',
    cwd: ROOT_DIR,
    env: { ...process.env, TERM: process.env.TERM || 'xterm-256color' }
  });
  child.unref();
}

function handleError(res, error) {
  res.status(400).json({ ok: false, error: error.message || '요청을 처리할 수 없습니다.' });
}

function getOrCreatePipelineState(projectDir, jobId) {
  const key = pipelineKey(projectDir, jobId);
  let state = pipelineStates.get(key);
  if (!state) {
    state = createPipelineState(projectDir, jobId);
    state.status = 'idle';
    state.currentStep = null;
    pipelineStates.set(key, state);
  }
  return state;
}

async function requireArtifacts(projectDir, jobId, names, message) {
  const requirements = await allArtifactsExist(projectDir, jobId, names);
  if (!requirements.ok) {
    throw new Error(`${message} 누락: ${requirements.missing.join(', ')}`);
  }
}

async function sendManualStage(projectDir, jobId, inputKo, stageId) {
  const stage = stageById(stageId);
  if (!stage) {
    throw new Error('허용되지 않은 단계입니다.');
  }
  const state = getOrCreatePipelineState(projectDir, jobId);
  if (ACTIVE_PIPELINE_STATES.has(state.status)) {
    throw new Error('이미 실행 중인 단계가 있습니다.');
  }
  state.status = stage.state;
  state.error = null;
  state.detectedIssue = null;
  state.finishedAt = null;
  setStep(state, stage.id, stage.label, 'running');
  const result = await sendToWindow(stage.role, projectDir, jobId, inputKo);
  await appendPipelineLog(projectDir, jobId, stage.id, `${result.stdout || ''}${result.stderr || ''}${result.message || ''}`);
  if (!result.ok) {
    state.status = 'failed';
    state.error = result.message || result.stderr || 'tmux 전송 실패';
    state.finishedAt = new Date().toISOString();
    setStep(state, stage.id, stage.label, 'failed', state.error);
  }
  await refreshPipelineArtifacts(state);
  return { state, result };
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
    const target = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'request.ko.md'));
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
    if (existing && ACTIVE_PIPELINE_STATES.has(existing.status)) {
      res.status(409).json({ ok: false, error: '이 작업의 파이프라인이 이미 실행 중입니다.' });
      return;
    }

    const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'request.ko.md'));
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
        message: 'Claude → Codex → Claude 전체 실행을 시작했습니다.',
        step: state.currentStep,
        detectedIssue: null,
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
        detectedIssue: null,
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
      await refreshDetectedIssue(state);
      markTimedOutRunningStep(state);
      await refreshPipelineArtifacts(state);
      if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
        await updateReviewSummary(projectDir, jobId, state);
      }
      res.json(await publicPipelineState(state));
      return;
    }

    res.json(await publicIdlePipelineState(projectDir, jobId));
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
      label: TMUX_WINDOW_LABELS[name] || name,
      aiRole: name === 'claude' || name === 'codex',
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

app.get('/api/tmux/approval-context', async (req, res) => {
  try {
    const windowName = validateAiTmuxWindow(req.query.window);
    const context = await buildApprovalContext(windowName, typeof req.query.step === 'string' ? req.query.step : null);
    if (!context) {
      res.status(404).json({ ok: false, error: '실제 승인 프롬프트를 찾지 못했습니다.' });
      return;
    }
    res.json({ ok: true, approvalContext: context });
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
    res.json({
      ok: true,
      output: 'GUI 서버 재시작 요청 완료\n3~5초 뒤 자동 확인합니다.',
      logPath: GUI_RESTART_LOG
    });
    setImmediate(scheduleGuiRestart);
  } catch (error) {
    handleError(res, error);
  }
});

for (const [endpoint, role] of [
  ['/api/send/claude-plan', 'claude-plan'],
  ['/api/send/codex-implement', 'codex-implement'],
  ['/api/send/claude-review', 'claude-review'],
  ['/api/send/codex-review-fix', 'codex-review-fix'],
  ['/api/send/claude-re-review', 'claude-re-review']
]) {
  app.post(endpoint, async (req, res) => {
    try {
      const projectDir = await resolveProjectDir(req.body.projectDir);
      const jobId = validateJobId(req.body.jobId);
      const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
      if (role === 'codex-implement') {
        await requireArtifacts(projectDir, jobId, ['plan.md', 'codex-task.md'], 'Claude 계획이 아직 완료되지 않았습니다. plan.md와 codex-task.md가 생성된 뒤 Codex를 실행할 수 있습니다.');
      }
      if (role === 'claude-review') {
        await requireArtifacts(projectDir, jobId, ['patch.md'], 'patch.md가 생성된 뒤 Claude 리뷰를 실행할 수 있습니다.');
      }
      if (role === 'codex-review-fix') {
        await requireArtifacts(projectDir, jobId, ['patch.md', 'review.md'], 'patch.md와 review.md가 생성된 뒤 Codex 리뷰 반영을 실행할 수 있습니다.');
      }
      if (role === 'claude-re-review') {
        await requireArtifacts(projectDir, jobId, ['patch.md', 'review.md', 'status.md'], 'Codex 리뷰 반영 상태가 생성된 뒤 Claude 재리뷰를 실행할 수 있습니다.');
      }
      const stage = stageById(role);
      const { state, result } = stage
        ? await sendManualStage(projectDir, jobId, inputKo, role)
        : { state: null, result: await sendToWindow(role, projectDir, jobId, inputKo) };
      res.json({
        ...cleanOutput(result),
        pipeline: state ? (await publicPipelineState(state)).status : null
      });
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

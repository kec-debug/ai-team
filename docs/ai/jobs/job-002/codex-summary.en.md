# Codex Summary

## Files

- `web/package.json` — adds the local Express app package and start script.
- `web/package-lock.json` — locks the Express dependency tree installed for verification.
- `web/.gitignore` — keeps installed local dependencies out of git.
- `web/server.js` — implements the safe predefined GUI API for tmux, job files, git status/diff, and job artifacts.
- `web/public/index.html` — adds the Korean single-page browser UI.
- `web/public/app.js` — wires UI actions to the predefined API endpoints.
- `web/public/style.css` — styles the browser control center.
- `README.md` — documents GUI installation, startup, scope, and safety boundaries.

## Notes

- The server binds to `127.0.0.1` by default and uses port `3100` by default.
- No arbitrary shell command input is exposed.
- Script execution uses fixed script paths, tmux sends target fixed existing window names, and git endpoints use fixed read-only arguments.
- Artifact reads are restricted to files inside the selected project's `docs/ai/jobs/` tree and to known job artifact filenames.
- v1 does not implement commit, push, merge, auth, payment, production infra, database migration, secret, token, or `.env` automation.

## Verification

- `node --check web/server.js`
- `node --check web/public/app.js`
- `npm install` (completed; 0 vulnerabilities reported)
- `npm start` (server running at `http://127.0.0.1:3100`)
- Verified live `GET /api/status`, `GET /api/artifacts`, and `GET /api/git/status`.
- Verified `GET /api/artifact` rejects a path traversal request.

## Verdict

READY FOR REVIEW

---
name: doc-commit-push
description: Analyze recent code changes in a git repo, update CLAUDE.md and README.md to reflect current state, then commit and push. Use when the user asks to update docs, sync documentation with code changes, refresh project docs, or says "update CLAUDE.md/README.md and push".
---

# Doc Commit Push

Update a project's CLAUDE.md and README.md to reflect the current codebase, then commit & push.

## Workflow

### Step 1: Assess changes

1. Run `git diff HEAD~5..HEAD --stat` (or appropriate range) to see recent changes.
2. Read the current `CLAUDE.md` and `README.md`.
3. Identify what's outdated or missing — new services, changed ports, renamed files, updated workflows, removed features.

### Step 2: Update CLAUDE.md

CLAUDE.md is for **Claude Code / AI agents** — focus on:
- Project architecture and service topology
- Key file paths and their purposes
- Common commands (build, test, deploy)
- Environment variables and configuration
- Important patterns and conventions

Rules:
- Keep it factual and concise — no marketing language.
- Only add/change sections that are affected by the code changes.
- Do not remove information that is still accurate.

### Step 3: Update README.md

README.md is for **human developers** — focus on:
- Project description and purpose
- Quick start / setup instructions
- Service architecture overview
- Configuration and environment variables

Rules:
- Use 繁體中文 for user-facing text (matching existing repo convention).
- Keep formatting consistent with the existing file.
- Only update sections affected by code changes.

### Step 4: Scan for sensitive data

Before committing, scan both files for:
- **Absolute paths** — `/Users/<username>/...` or any user-specific path
- **Phone numbers** — real personal or service numbers (e.g. `+886...`)
- **API keys / tokens** — any string resembling a secret (`sk-...`, bearer tokens)
- **Email addresses** — personal emails
- **Hardcoded credentials** — passwords, auth tokens

If found, sanitize before proceeding:
- Absolute paths → use relative paths or generic placeholders (e.g. `~/...`)
- Secrets → `YOUR_<NAME>_HERE`
- Phone numbers → remove or replace with placeholder

### Step 5: Commit & push

1. Stage only the doc files: `git add CLAUDE.md README.md`
2. Commit with a descriptive message:
   ```
   docs: 更新 CLAUDE.md / README.md — <簡述變更>
   ```
3. Push to the current branch.

### Step 6: Push to public repo (optional)

Ask the user: **「是否也要推到 public repo？」**

If yes:
1. Check available remotes with `git remote -v`.
2. Confirm the sanitization in Step 4 is complete — public repo must have zero sensitive data.
3. Push to the public remote:
   ```bash
   git push <public-remote> <branch>
   ```

## Notes

- If the repo has no CLAUDE.md or README.md, ask the user before creating one from scratch.
- If there are unstaged code changes, only update docs for committed changes — do not commit code files.
- Always read both files before editing to preserve existing structure and style.

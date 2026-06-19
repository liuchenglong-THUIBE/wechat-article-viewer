# Agent-Friendly Open Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repository easy for humans and generic coding agents to clone, configure, schedule, troubleshoot, and publish without requiring MCP or platform-specific Skills.

**Architecture:** Keep the existing crawler, CLI, frontend, and current local launchd setup intact. Add documentation and reusable templates around the existing command surface so agents can operate the project safely through documented commands and files.

**Tech Stack:** Python 3.9+, Click CLI, Playwright, OpenAI-compatible LLM APIs, static HTML/CSS/JavaScript frontend, macOS launchd templates, Markdown documentation.

---

## File Map

- Modify: `README.md` as the public project overview and navigation hub.
- Create: `AGENTS.md` as the agent-facing operating manual.
- Create: `QUICKSTART.md` as the shortest human setup path.
- Create: `TROUBLESHOOTING.md` as the failure recovery guide.
- Modify: `.env.example` to use `WECHAT_READER_FRONTEND_DIR=frontend`.
- Modify: `config/config.json.example` to use `"frontend_dir": "frontend"`.
- Create: `scripts/daily_update.example.sh` as a reusable daily update template.
- Create: `launchd/com.wechat-reader.daily-update.plist.template` as a reusable launchd template.
- Modify: `.gitignore` to exclude `.daily-update.lock` and the whole `data/` runtime directory.

## Task 1: Configuration Example Hygiene

**Files:**
- Modify: `.env.example`
- Modify: `config/config.json.example`
- Modify: `.gitignore`

- [ ] **Step 1: Update `.env.example` frontend path**

Change:

```dotenv
WECHAT_READER_FRONTEND_DIR=frontend/api
```

To:

```dotenv
WECHAT_READER_FRONTEND_DIR=frontend
```

Expected: examples match `Config.get_frontend_api_dir()`, which appends `/api`.

- [ ] **Step 2: Update `config/config.json.example` frontend path**

Change:

```json
"frontend_dir": "frontend/api"
```

To:

```json
"frontend_dir": "frontend"
```

Expected: users who copy the example write data to `frontend/api`, not `frontend/api/api`.

- [ ] **Step 3: Update `.gitignore` runtime entries**

Ensure the project-specific section contains:

```gitignore
# Project specific
data/
config.json
*.log
logs/
backups/
.daily-update.lock/
```

Expected: local sessions, logs, backups, and lock directories are not committed.

- [ ] **Step 4: Verify changed lines**

Run:

```bash
grep -n "FRONTEND_DIR\\|frontend_dir" .env.example config/config.json.example
grep -n "data/\\|backups/\\|daily-update" .gitignore
```

Expected: frontend examples use `frontend`; `.gitignore` includes `data/`, `backups/`, and `.daily-update.lock/`.

## Task 2: Reusable Schedule Templates

**Files:**
- Create: `scripts/daily_update.example.sh`
- Create: `launchd/com.wechat-reader.daily-update.plist.template`

- [ ] **Step 1: Create `scripts/daily_update.example.sh`**

Add this complete template:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="__PROJECT_DIR__"
PYTHON_BIN="__PYTHON_BIN__"
DAYS="__DAYS__"
LOG_DIR="$PROJECT_DIR/logs"
LOCK_DIR="$PROJECT_DIR/.daily-update.lock"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

mkdir -p "$LOG_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] daily update is already running, skip"
  exit 0
fi

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR/src"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] daily update started"
"$PYTHON_BIN" -m wechat_reader weekly-update --days "$DAYS"
"$PYTHON_BIN" -m wechat_reader export --sync
echo "[$(date '+%Y-%m-%d %H:%M:%S')] daily update finished"
```

- [ ] **Step 2: Create `launchd/com.wechat-reader.daily-update.plist.template`**

Add this complete template:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.wechat-reader.daily-update</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>__PROJECT_DIR__/scripts/daily_update.sh</string>
  </array>

  <key>WorkingDirectory</key>
  <string>__PROJECT_DIR__</string>

  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>__HOUR__</integer>
    <key>Minute</key>
    <integer>__MINUTE__</integer>
  </dict>

  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>

  <key>StandardOutPath</key>
  <string>__PROJECT_DIR__/logs/daily-update.log</string>

  <key>StandardErrorPath</key>
  <string>__PROJECT_DIR__/logs/daily-update.err.log</string>

  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
```

- [ ] **Step 3: Validate template syntax**

Run:

```bash
bash -n scripts/daily_update.example.sh
grep -n "__PROJECT_DIR__\\|__PYTHON_BIN__\\|__DAYS__" scripts/daily_update.example.sh
grep -n "__PROJECT_DIR__\\|__HOUR__\\|__MINUTE__" launchd/com.wechat-reader.daily-update.plist.template
```

Expected: Bash syntax passes and placeholders are visible.

## Task 3: Agent And User Documentation

**Files:**
- Modify: `README.md`
- Create: `AGENTS.md`
- Create: `QUICKSTART.md`
- Create: `TROUBLESHOOTING.md`

- [ ] **Step 1: Rewrite `README.md`**

Include sections:

```markdown
# WeChat Article Reader

Local-first tool for collecting WeChat public account articles, generating AI summaries, and publishing a static reading site.

## What It Does
## Who This Is For
## How It Works
## Quick Start
## Agent-Friendly Usage
## Common Commands
## Daily Automation
## Publishing
## Configuration
## Safety Notes
## Troubleshooting
## Project Structure
```

Expected: README links to `QUICKSTART.md`, `AGENTS.md`, and `TROUBLESHOOTING.md`.

- [ ] **Step 2: Add `AGENTS.md`**

Include:

```markdown
# AGENTS.md

## Purpose
## Read First
## Safety Rules
## Common Commands
## Daily Schedule Setup
## Logs
## Recommended User Prompt
```

Expected: the file tells agents not to commit `.env`, `config.json`, `data/session.json`, logs, backups, or local runtime files.

- [ ] **Step 3: Add `QUICKSTART.md`**

Include clone, venv, install, Playwright, config, init, login-through-update command sequence.

Expected: a new user can follow it from a fresh clone to one successful update.

- [ ] **Step 4: Add `TROUBLESHOOTING.md`**

Include failure sections for auth, LLM, no articles, extraction failure, Git sync, launchd, logs, and safe reruns.

Expected: agents have a deterministic place to inspect common failures.

## Task 4: Verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Search for stale path examples**

Run:

```bash
grep -R "frontend/api/api\\|WECHAT_READER_FRONTEND_DIR=frontend/api" README.md AGENTS.md QUICKSTART.md TROUBLESHOOTING.md .env.example config/config.json.example
```

Expected: no matches.

- [ ] **Step 2: Confirm current personal automation remains untouched**

Run:

```bash
test -f scripts/daily_update.sh
test -f launchd/com.wechat-reader.daily-update.plist
```

Expected: both commands exit with code 0.

- [ ] **Step 3: Check CLI help still works**

Run:

```bash
PYTHONPATH=src /opt/miniconda3/bin/python3 -m wechat_reader --help
```

Expected: command exits with code 0 and shows `微信公众号阅读器`.

- [ ] **Step 4: Review git diff**

Run:

```bash
git diff -- README.md AGENTS.md QUICKSTART.md TROUBLESHOOTING.md .env.example config/config.json.example scripts/daily_update.example.sh launchd/com.wechat-reader.daily-update.plist.template .gitignore
```

Expected: diff only contains documentation, examples, templates, and ignore hygiene changes.

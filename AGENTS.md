# AGENTS.md

This file is for AI coding agents operating this repository.

## Purpose

This project is a local CLI tool for collecting WeChat public account articles, generating AI summaries, and updating a static reading website.

The safest operating model is:

1. Keep WeChat login state and API keys local.
2. Use documented CLI commands.
3. Use templates for local schedules.
4. Read logs before retrying failed work.
5. Preserve user-owned data in `frontend/api`.

## Read First

Before changing anything, read:

- `README.md`
- `QUICKSTART.md`
- `TROUBLESHOOTING.md`
- `config/config.json.example`
- `.env.example`

If the user asks for daily automation, inspect:

- `scripts/daily_update.example.sh`
- `launchd/com.wechat-reader.daily-update.plist.template`

## Safety Rules

- Do not commit `.env`.
- Do not commit `config.json`.
- Do not commit `data/session.json` or any file under `data/`.
- Do not commit `logs/`, `backups/`, or `.daily-update.lock/`.
- Do not delete `frontend/api/articles.json`, `accounts.json`, or `monitors.json` unless the user explicitly asks.
- Do not overwrite an existing working `scripts/daily_update.sh` or launchd plist without showing the diff to the user.
- Do not run destructive Git commands such as `git reset --hard` or `git checkout --` unless the user explicitly asks.
- If WeChat login is required, stop and ask the user to complete the QR-code login in a normal browser or terminal session.

## Common Commands

Install from source:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

Initialize:

```bash
wechat-reader init
```

Configure LLM:

```bash
wechat-reader config set llm_api_key "your-api-key"
wechat-reader config set llm_model "minimax/minimax-m2.5:free"
wechat-reader config set llm_base_url "https://openrouter.ai/api/v1"
```

Manage monitors:

```bash
wechat-reader monitor add "公众号名称"
wechat-reader monitor list
wechat-reader monitor remove "公众号名称"
```

Run update:

```bash
wechat-reader weekly-update --days 2
```

Publish frontend:

```bash
wechat-reader export --sync
```

Run from source without installing:

```bash
PYTHONPATH=src python3 -m wechat_reader weekly-update --days 2
PYTHONPATH=src python3 -m wechat_reader export --sync
```

## Daily Schedule Setup

Prefer the provided templates instead of inventing new launchd files.

1. Copy `scripts/daily_update.example.sh` to `scripts/daily_update.sh`.
2. Replace `__PROJECT_DIR__`, `__PYTHON_BIN__`, and `__DAYS__`.
3. Copy `launchd/com.wechat-reader.daily-update.plist.template` to `~/Library/LaunchAgents/com.wechat-reader.daily-update.plist`.
4. Replace `__PROJECT_DIR__`, `__HOUR__`, and `__MINUTE__`.
5. Load the plist with `launchctl bootstrap`.

Recommended default:

```text
__DAYS__=2
__HOUR__=10
__MINUTE__=0
```

Use `--days 2` for daily updates unless the user prefers a stricter one-day window. Link-based deduplication avoids duplicate articles while reducing boundary misses.

## Logs

Default schedule logs:

```bash
tail -f logs/daily-update.log
tail -f logs/daily-update.err.log
```

If an update partially fails, check whether the failure is:

- Authentication failure.
- LLM summary failure.
- Article content extraction failure.
- Git sync failure.

Content extraction failures for individual articles are partial failures. They do not always mean the whole update is broken.

## Recommended User Prompt

```text
Please read README.md, AGENTS.md, QUICKSTART.md, and TROUBLESHOOTING.md.
Help me configure this WeChat Article Reader locally.
Use my LLM API key, add my monitored public accounts, run one update test,
and install a daily 10:00 local schedule.
Do not commit .env, config.json, data/session.json, logs, backups, or local runtime files.
```

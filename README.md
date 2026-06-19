# WeChat Article Reader

Local-first tool for collecting WeChat public account articles, generating AI summaries, and publishing a static reading site.

This repository is designed for both humans and AI coding agents. You can operate it manually from the command line, or ask an agent such as Codex, TRAE, Claude Code, or OpenClaw to read the docs and run the documented commands.

## What It Does

- Collects recent articles from monitored WeChat public accounts.
- Reuses a local WeChat public platform login session.
- Extracts article text and generates AI summaries with an OpenAI-compatible API.
- Stores static JSON data in `frontend/api`.
- Serves a pure static reading frontend from `frontend`.
- Optionally syncs the frontend to GitHub for Cloudflare Pages or another static host.
- Supports local daily automation through macOS `launchd` templates.

## Who This Is For

- People who want a personal WeChat article reading website.
- People who prefer local automation instead of a hosted crawler service.
- Developers who want to let an AI coding agent configure and operate the project.
- Users who are comfortable scanning a WeChat login QR code and managing their own API keys.

This project is not a hosted SaaS. WeChat login state, LLM keys, and Git credentials remain on your machine.

## How It Works

1. You configure an OpenAI-compatible LLM provider.
2. You log into WeChat public platform locally.
3. You add public accounts to the monitor list.
4. `wechat-reader weekly-update --days N` fetches recent article links.
5. The crawler extracts article content and generates summaries.
6. Data is written to `frontend/api/articles.json`, `accounts.json`, and `monitors.json`.
7. `wechat-reader export --sync` can push the static frontend to GitHub.

## Quick Start

For a short copy-and-run setup path, read [QUICKSTART.md](QUICKSTART.md).

Basic flow:

```bash
git clone https://github.com/yourusername/wechat-article-reader.git
cd wechat-article-reader

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium

cp .env.example .env
wechat-reader init
wechat-reader monitor add "晚点LatePost"
wechat-reader weekly-update --days 2
wechat-reader export --sync
```

If authentication is required, run an update command in a normal terminal and follow the WeChat login prompt.

## Agent-Friendly Usage

If you want an AI coding agent to operate this project, ask it to read [AGENTS.md](AGENTS.md) first.

Recommended prompt:

```text
Please read README.md, AGENTS.md, QUICKSTART.md, and TROUBLESHOOTING.md.
Help me configure this WeChat Article Reader locally, add my monitored public accounts,
run one update test, and install a daily 10:00 local schedule.
Do not commit .env, config.json, data/session.json, logs, backups, or local runtime files.
```

## Common Commands

```bash
# Initialize directories and config
wechat-reader init

# Configure LLM values
wechat-reader config set llm_api_key "your-api-key"
wechat-reader config set llm_model "minimax/minimax-m2.5:free"
wechat-reader config set llm_base_url "https://openrouter.ai/api/v1"

# Manage monitored public accounts
wechat-reader monitor add "公众号名称"
wechat-reader monitor list
wechat-reader monitor remove "公众号名称"

# Collect one account or one article
wechat-reader collect account "公众号名称" --recent 7
wechat-reader collect article "https://mp.weixin.qq.com/s/..."

# Update all monitored accounts
wechat-reader weekly-update --days 2

# Sync the static frontend to Git
wechat-reader export --sync
```

## Daily Automation

The recommended automation is local. This works better than a cloud-only job because WeChat article collection depends on local login state.

Reusable templates are provided:

- `scripts/daily_update.example.sh`
- `launchd/com.wechat-reader.daily-update.plist.template`

Typical macOS setup:

```bash
cp scripts/daily_update.example.sh scripts/daily_update.sh
chmod +x scripts/daily_update.sh
```

Replace placeholders in `scripts/daily_update.sh`:

```text
__PROJECT_DIR__  absolute project path
__PYTHON_BIN__   Python interpreter path, for example /path/to/.venv/bin/python
__DAYS__         recommended value: 2
```

Then copy and fill the launchd template:

```bash
cp launchd/com.wechat-reader.daily-update.plist.template \
  "$HOME/Library/LaunchAgents/com.wechat-reader.daily-update.plist"
```

Replace placeholders:

```text
__PROJECT_DIR__  absolute project path
__HOUR__         10
__MINUTE__       0
```

Load the schedule:

```bash
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.wechat-reader.daily-update.plist"
launchctl enable "gui/$(id -u)/com.wechat-reader.daily-update"
```

Check status:

```bash
launchctl print "gui/$(id -u)/com.wechat-reader.daily-update"
```

View logs:

```bash
tail -f logs/daily-update.log
tail -f logs/daily-update.err.log
```

## Publishing

The frontend is a static site in `frontend`.

For Cloudflare Pages:

- Build command: `echo "No build needed"`
- Build output directory: `frontend`

`wechat-reader export --sync` uses Git to publish the frontend. Review your repository layout before enabling this, because the current implementation uses a subtree-based push for `frontend`.

## Configuration

Use either `config.json` or environment variables.

Copy the example:

```bash
cp config/config.json.example config.json
```

Important path rule:

```json
{
  "frontend_dir": "frontend"
}
```

The program appends `/api` internally, so data is written to `frontend/api`.

Environment variable equivalent:

```bash
WECHAT_READER_FRONTEND_DIR=frontend
```

Supported OpenAI-compatible providers include OpenRouter, OpenAI, Doubao, Qwen-compatible gateways, and other compatible endpoints.

## Safety Notes

Do not commit:

- `.env`
- `config.json`
- `data/session.json`
- `logs/`
- `backups/`
- local launchd files that contain private machine paths

The project `.gitignore` excludes common local runtime files, but always review `git status` before committing or pushing.

## Troubleshooting

Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common failures:

- WeChat login expired.
- No articles found.
- Article content extraction failed.
- LLM summary failed.
- GitHub push failed.
- launchd did not run.

## Project Structure

```text
wechat-article-reader/
├── AGENTS.md
├── QUICKSTART.md
├── TROUBLESHOOTING.md
├── config/
│   └── config.json.example
├── frontend/
│   ├── api/
│   │   ├── accounts.json
│   │   ├── articles.json
│   │   └── monitors.json
│   ├── app.js
│   ├── index.html
│   └── style.css
├── launchd/
│   ├── com.wechat-reader.daily-update.plist
│   └── com.wechat-reader.daily-update.plist.template
├── scripts/
│   ├── daily_update.sh
│   └── daily_update.example.sh
└── src/
    └── wechat_reader/
```

## License

MIT License

# Agent-Friendly Open Source Design

## Goal

Turn this repository into an agent-friendly open source project that people can clone, configure, and operate with their own coding agents such as Codex, TRAE, Claude Code, or OpenClaw.

The project should remain a normal local CLI application. It should not require MCP, a platform-specific Skill, or a hosted service. The main improvement is documentation and reusable templates so agents can reliably install, configure, update, schedule, debug, and publish the reader.

## Selected Approach

Use the "documentation plus templated scripts" approach.

This keeps the current crawler and CLI behavior intact while adding:

- Clear human-facing setup documentation.
- Agent-facing operating instructions.
- Troubleshooting guidance.
- Generic schedule script templates.
- Safer configuration examples.
- Better repository hygiene for secrets and local runtime files.

This approach minimizes implementation risk and preserves the current daily local automation.

## Non-Goals

- Do not build an MCP server in this phase.
- Do not build TRAE/Codex/OpenClaw-specific Skills in this phase.
- Do not refactor crawler internals in this phase.
- Do not replace the current working macOS launchd automation.
- Do not publish user secrets, cookies, local logs, or private runtime data.

## Target Users

### Human Users

Users who clone the repository and want to run a personal WeChat public account article reader. They need concise installation, configuration, login, update, schedule, and deployment instructions.

### Coding Agents

Agents that read the repository and execute commands on behalf of users. They need deterministic command recipes, clear file ownership rules, fixed log paths, and explicit "do not touch" safety guidance.

## Repository Changes

### README.md

Rewrite the README as the main project landing page:

- Explain what the project does.
- Explain local-first design and WeChat login requirements.
- Link to quick start, agent guide, and troubleshooting guide.
- Show common commands.
- Explain static frontend publishing through GitHub and Cloudflare Pages.
- Clarify that the project can be operated manually or by an AI coding agent.

### AGENTS.md

Add an agent-specific operation manual:

- State the project purpose and safe operating rules.
- List common commands for install, init, login, monitor management, update, export, schedule setup, and logs.
- Tell agents not to commit `.env`, `config.json`, `data/session.json`, logs, backups, or local runtime files.
- Tell agents to prefer documented scripts and templates instead of inventing launchd or cron files.
- Include a recommended user prompt that people can give to their agent after cloning.

### QUICKSTART.md

Add a short guide for first-time setup:

- Clone repository.
- Create Python environment.
- Install package in editable mode.
- Install Playwright browser.
- Copy `.env.example` or configure `config.json`.
- Run `wechat-reader init`.
- Log in through WeChat public platform flow.
- Add monitors.
- Run one update.
- Export and sync site.

### TROUBLESHOOTING.md

Add a troubleshooting guide:

- Login session expired.
- LLM API key or model failure.
- No articles found.
- Article content extraction failed.
- GitHub push or Cloudflare deployment failed.
- launchd permission and PATH issues.
- How to inspect logs.
- How to safely rerun a failed update.

### Configuration Examples

Fix examples to avoid path confusion:

- Use `frontend_dir: "frontend"` in JSON examples.
- Use `WECHAT_READER_FRONTEND_DIR=frontend` in `.env.example`.
- Explain that the code writes data to `frontend/api`.

### Script Templates

Add generic templates while keeping the existing working script untouched:

- `scripts/daily_update.example.sh`
- `launchd/com.wechat-reader.daily-update.plist.template`

The templates should use placeholder values such as:

- `__PROJECT_DIR__`
- `__PYTHON_BIN__`
- `__DAYS__`
- `__HOUR__`
- `__MINUTE__`

This lets users or agents copy and fill templates without overwriting the current local automation.

### Git Ignore Hygiene

Update `.gitignore` if needed so local runtime files are excluded:

- `.env`
- `config.json`
- `data/`
- `logs/`
- `backups/`
- `.daily-update.lock`
- Python caches and virtual environments.

Do not ignore the reusable docs, templates, or empty frontend API starter files needed for the open source repository.

## Data Flow

The documented operating flow is:

1. User or agent configures LLM and local project settings.
2. User logs into WeChat public platform and stores local session data.
3. User or agent adds public accounts to the monitor list.
4. Update command reads monitor list and fetches recent article links.
5. Article extraction and LLM summary generation update `frontend/api/articles.json`.
6. Export command syncs the static frontend to GitHub.
7. Cloudflare Pages or another static host deploys the updated frontend.

## Schedule Flow

The recommended daily schedule remains local:

1. Copy `scripts/daily_update.example.sh` to `scripts/daily_update.sh`.
2. Replace placeholders with local paths and desired day range.
3. Copy `launchd/com.wechat-reader.daily-update.plist.template` to a user LaunchAgents plist.
4. Replace placeholders.
5. Load with `launchctl`.
6. Check logs in `logs/daily-update.log` and `logs/daily-update.err.log`.

The default recommendation for new users is `--days 2` for daily updates because link-based deduplication reduces duplicate risk and lowers missed-article risk around day boundaries. Existing local users may keep `--days 1` if they prefer.

## Error Handling Guidance

Documentation should teach agents to:

- Stop and ask the user to scan a QR code if login is required.
- Avoid deleting local session data unless the user asks.
- Read logs before rerunning failed tasks.
- Treat content extraction failures as partial failures, not total schedule failures.
- Run `wechat-reader export --sync` only after a successful or acceptable update.
- Preserve user-edited monitor and article JSON files.

## Testing And Verification

After implementation, verify:

- Markdown files render and contain no stale hardcoded personal paths in reusable instructions.
- `.env.example` and `config/config.json.example` use `frontend`, not `frontend/api`.
- Existing `scripts/daily_update.sh` remains present for the current user workflow.
- New templates do not overwrite the current launchd setup.
- `wechat-reader --help` still works.
- `python -m wechat_reader --help` still works with `PYTHONPATH=src`.

## Rollout

This phase should be a documentation-first commit. It should make the project easier to share without changing core crawler behavior.

Future phases may add:

- `wechat-reader login`
- `wechat-reader doctor`
- `wechat-reader refresh-fakeids`
- `wechat-reader schedule install/status/logs/uninstall`
- MCP or platform-specific Skill wrappers

Those are intentionally out of scope for this phase.

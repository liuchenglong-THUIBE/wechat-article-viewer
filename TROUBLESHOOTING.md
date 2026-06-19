# Troubleshooting

Use this guide when an update, schedule, login, summary, or publishing step fails.

## First Checks

Run commands from the repository root.

```bash
pwd
wechat-reader --help
wechat-reader config list
wechat-reader monitor list
```

If running from source without installation:

```bash
PYTHONPATH=src python3 -m wechat_reader --help
```

## WeChat Login Expired

Symptoms:

- Update asks for login.
- Session validation fails.
- Requests to WeChat public platform return login or permission pages.

What to do:

```bash
wechat-reader weekly-update --days 1
```

Complete the QR-code login flow if prompted. The session is stored locally under `data/` and must not be committed.

If an AI agent is operating the project, it should stop and ask the user to complete login.

## LLM API Key Or Model Failure

Symptoms:

- Article links are found, but summaries fail.
- Logs mention API key, authentication, model, quota, or base URL errors.

Check config:

```bash
wechat-reader config get llm_api_key
wechat-reader config get llm_model
wechat-reader config get llm_base_url
```

Set values:

```bash
wechat-reader config set llm_api_key "your-api-key"
wechat-reader config set llm_model "minimax/minimax-m2.5:free"
wechat-reader config set llm_base_url "https://openrouter.ai/api/v1"
```

If using `.env`, reload it:

```bash
set -a
source .env
set +a
```

## No Articles Found

Symptoms:

- `weekly-update` checks accounts but adds no articles.
- Logs frequently say article time is older than the threshold.

Possible reasons:

- Monitored accounts did not publish in the selected window.
- Articles were already collected and deduplicated by link.
- The update window is too narrow around day boundaries.
- The public account fakeid is wrong or stale.

Try:

```bash
wechat-reader weekly-update --days 2
```

Then inspect `frontend/api/articles.json` and logs.

## Article Content Extraction Failed

Symptoms:

- Logs contain `未找到文章内容区域`.
- Logs contain `提取内容失败`.
- Candidate articles are found but not added.

Common causes:

- The article has no normal text body.
- The article is deleted, restricted, or only contains images/video.
- WeChat returned a verification, redirect, or non-standard page.
- The article template does not contain the expected `#js_content` area.

This is usually a partial failure. Other articles in the same update can still succeed.

If needed, open the failed link manually in a browser and confirm whether readable text exists.

## GitHub Push Or Static Publishing Failed

Symptoms:

- `wechat-reader export --sync` fails.
- Git asks for credentials.
- Cloudflare Pages does not update.

Check Git:

```bash
git status
git remote -v
git branch --show-current
```

Check whether the frontend data changed:

```bash
git diff -- frontend/api/articles.json frontend/api/accounts.json frontend/api/monitors.json
```

Run sync:

```bash
wechat-reader export --sync
```

For Cloudflare Pages, verify:

- Build command: `echo "No build needed"`
- Build output directory: `frontend`
- The connected branch matches your publishing strategy.

## launchd Did Not Run

Symptoms:

- Daily update did not happen.
- No log output was written.
- `launchctl print` shows an error.

Check plist:

```bash
plutil -lint "$HOME/Library/LaunchAgents/com.wechat-reader.daily-update.plist"
```

Check status:

```bash
launchctl print "gui/$(id -u)/com.wechat-reader.daily-update"
```

Run once:

```bash
launchctl kickstart -k "gui/$(id -u)/com.wechat-reader.daily-update"
```

Check logs:

```bash
tail -f logs/daily-update.log
tail -f logs/daily-update.err.log
```

On macOS, avoid scheduling directly from privacy-protected directories if launchd reports `Operation not permitted`. Move the runtime copy to a normal user directory and update `__PROJECT_DIR__`.

## PATH Or Python Not Found In Schedule

Symptoms:

- Manual update works.
- Scheduled update fails with `python: command not found` or module import errors.

Use an absolute Python path in `scripts/daily_update.sh`:

```bash
which python
```

Then set:

```bash
PYTHON_BIN="/absolute/path/to/python"
```

If running from source, keep:

```bash
export PYTHONPATH="$PROJECT_DIR/src"
```

## Safe Rerun

It is safe to rerun updates because articles are deduplicated by link.

```bash
wechat-reader weekly-update --days 2
wechat-reader export --sync
```

Do not delete `frontend/api/articles.json` to fix a failed run unless the user explicitly wants to rebuild the dataset.

## Files That Should Stay Local

Do not commit:

- `.env`
- `config.json`
- `data/`
- `logs/`
- `backups/`
- `.daily-update.lock/`

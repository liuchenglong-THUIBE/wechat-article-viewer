# Quick Start

This guide gets a fresh clone to one successful local update.

## 1. Clone

```bash
git clone https://github.com/yourusername/wechat-article-reader.git
cd wechat-article-reader
```

## 2. Create Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
playwright install chromium
```

## 3. Configure

Choose one configuration method.

### Option A: Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
WECHAT_READER_LLM_API_KEY=your-api-key-here
WECHAT_READER_LLM_MODEL=minimax/minimax-m2.5:free
WECHAT_READER_LLM_BASE_URL=https://openrouter.ai/api/v1
WECHAT_READER_FRONTEND_DIR=frontend
```

Load it in your shell:

```bash
set -a
source .env
set +a
```

### Option B: config.json

```bash
cp config/config.json.example config.json
wechat-reader config set llm_api_key "your-api-key"
```

Important:

```json
{
  "frontend_dir": "frontend"
}
```

The program writes API data to `frontend/api`.

## 4. Initialize

```bash
wechat-reader init
```

This creates the frontend API data directory and writes the default local configuration.

## 5. Add Public Accounts

```bash
wechat-reader monitor add "晚点LatePost"
wechat-reader monitor add "腾讯研究院"
wechat-reader monitor list
```

## 6. Run One Update

```bash
wechat-reader weekly-update --days 2
```

If WeChat login is required, follow the QR-code login flow shown by the tool. Login state is stored locally and should not be committed.

## 7. Check Data

```bash
ls frontend/api
```

Expected files:

```text
accounts.json
articles.json
monitors.json
```

## 8. Publish Static Site

If your GitHub repository and static host are configured:

```bash
wechat-reader export --sync
```

For Cloudflare Pages:

- Build command: `echo "No build needed"`
- Build output directory: `frontend`

## 9. Optional Daily Schedule

Copy the reusable script template:

```bash
cp scripts/daily_update.example.sh scripts/daily_update.sh
chmod +x scripts/daily_update.sh
```

Replace:

```text
__PROJECT_DIR__  absolute path to this repository
__PYTHON_BIN__   absolute path to .venv/bin/python
__DAYS__         2
```

Copy the launchd template:

```bash
cp launchd/com.wechat-reader.daily-update.plist.template \
  "$HOME/Library/LaunchAgents/com.wechat-reader.daily-update.plist"
```

Replace:

```text
__PROJECT_DIR__  absolute path to this repository
__HOUR__         10
__MINUTE__       0
```

Load it:

```bash
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.wechat-reader.daily-update.plist"
launchctl enable "gui/$(id -u)/com.wechat-reader.daily-update"
```

Test once:

```bash
launchctl kickstart -k "gui/$(id -u)/com.wechat-reader.daily-update"
```

Check logs:

```bash
tail -f logs/daily-update.log
tail -f logs/daily-update.err.log
```

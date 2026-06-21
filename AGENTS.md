# AGENTS.md

这个文件面向操作本仓库的 AI 编程 Agent，包括 Codex、TRAE、Claude Code、OpenClaw 等。

## 项目目的

本项目是一个本地 CLI 工具，用于采集微信公众号文章、生成 AI 摘要，并更新一个静态阅读网站。

最安全的操作方式是：

1. 微信登录状态和 API Key 只保留在本地。
2. 优先使用文档中给出的 CLI 命令。
3. 配置本地定时任务时使用项目提供的模板。
4. 失败后先读取日志，再决定是否重试。
5. 保留用户在 `frontend/api` 下已有的数据。

## 修改前先阅读

在修改任何文件前，请先阅读：

- `README.md`
- `QUICKSTART.md`
- `TROUBLESHOOTING.md`
- `config/config.json.example`
- `.env.example`

如果用户要求配置每日自动化任务，请检查：

- `scripts/daily_update.example.sh`
- `launchd/com.wechat-reader.daily-update.plist.template`

## 安全规则

- 不要提交 `.env`。
- 不要提交 `config.json`。
- 不要提交 `data/session.json` 或 `data/` 下的任何文件。
- 不要提交 `logs/`、`backups/` 或 `.daily-update.lock/`。
- 除非用户明确要求，否则不要删除 `frontend/api/articles.json`、`accounts.json` 或 `monitors.json`。
- 不要直接覆盖已有可用的 `scripts/daily_update.sh` 或 launchd plist；如需修改，先向用户展示差异。
- 除非用户明确要求，否则不要执行 `git reset --hard`、`git checkout --` 等破坏性 Git 命令。
- 如果需要微信登录，请停止自动操作，并要求用户在普通浏览器或终端会话中完成二维码扫码登录。

## 常用命令

从源码安装：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

初始化：

```bash
wechat-reader init
```

配置 LLM：

```bash
wechat-reader config set llm_api_key "your-api-key"
wechat-reader config set llm_model "minimax/minimax-m2.5:free"
wechat-reader config set llm_base_url "https://openrouter.ai/api/v1"
```

管理监控公众号：

```bash
wechat-reader monitor add "公众号名称"
wechat-reader monitor list
wechat-reader monitor remove "公众号名称"
```

执行更新：

```bash
wechat-reader weekly-update --days 2
```

发布前端：

```bash
wechat-reader export --sync
```

不安装包，直接从源码运行：

```bash
PYTHONPATH=src python3 -m wechat_reader weekly-update --days 2
PYTHONPATH=src python3 -m wechat_reader export --sync
```

## 每日定时任务配置

优先使用项目提供的模板，不要临时发明新的 launchd 文件。

1. 复制 `scripts/daily_update.example.sh` 到 `scripts/daily_update.sh`。
2. 替换 `__PROJECT_DIR__`、`__PYTHON_BIN__` 和 `__DAYS__`。
3. 复制 `launchd/com.wechat-reader.daily-update.plist.template` 到 `~/Library/LaunchAgents/com.wechat-reader.daily-update.plist`。
4. 替换 `__PROJECT_DIR__`、`__HOUR__` 和 `__MINUTE__`。
5. 使用 `launchctl bootstrap` 加载 plist。

推荐默认值：

```text
__DAYS__=2
__HOUR__=10
__MINUTE__=0
```

除非用户更希望严格只采集过去一天，否则每日更新建议使用 `--days 2`。系统会按文章链接去重，这样可以减少跨天边界漏抓的风险。

定时任务应使用 `weekly-update --no-login`。在该模式下，已有 session 有效则继续爬取；session 无效或无法验证时直接退出，不要自动打开浏览器等待扫码。

## 日志

默认定时任务日志：

```bash
tail -f logs/daily-update.log
tail -f logs/daily-update.err.log
```

如果更新部分失败，请判断失败类型：

- 微信登录失败。
- LLM 摘要生成失败。
- 文章正文解析失败。
- Git 同步失败。

单篇文章正文解析失败通常是局部失败，不一定表示整个更新任务不可用。

## 推荐给用户的提示词

```text
请先阅读 README.md、AGENTS.md、QUICKSTART.md 和 TROUBLESHOOTING.md。
请帮我在本地配置这个微信公众号文章阅读器。
使用我的 LLM API Key，添加我要监控的公众号，运行一次更新测试，
并安装每天 10:00 执行的本地定时任务。
不要提交 .env、config.json、data/session.json、logs、backups 或本地运行文件。
```

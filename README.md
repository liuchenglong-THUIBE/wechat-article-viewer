# 微信公众号文章阅读器

这是一个本地优先的微信公众号文章采集与阅读工具。它可以抓取已监控公众号的近期文章，使用 AI 生成摘要，并把结果发布成一个静态阅读网站。

这个仓库面向中国用户和中文使用场景设计。你既可以手动执行命令，也可以让 Codex、TRAE、Claude Code、OpenClaw 等 AI 编程 Agent 读取项目文档并按说明操作。

## 项目能做什么

- 采集已监控微信公众号的近期文章。
- 复用本地微信公众号平台登录状态。
- 提取文章正文，并通过 OpenAI 兼容接口生成 AI 摘要。
- 将静态 JSON 数据写入 `frontend/api`。
- 通过 `frontend` 提供纯静态阅读前端。
- 可选使用 GitHub、Cloudflare Pages 或其他静态托管服务发布网站。
- 提供 macOS `launchd` 模板，方便配置本地每日自动更新。

## 适合谁使用

- 想搭建个人微信公众号文章阅读网站的用户。
- 希望把采集逻辑留在本地，而不是依赖云端爬虫服务的用户。
- 想让 AI 编程 Agent 帮自己配置、运行和维护项目的开发者。
- 能自行扫码登录微信公众号平台，并管理自己 LLM API Key 的用户。

这个项目不是托管 SaaS。微信登录状态、LLM API Key、Git 凭据都会保留在你的本地机器上。

## 工作流程

1. 配置一个 OpenAI 兼容的 LLM 服务。
2. 在本地完成微信公众号平台登录。
3. 添加需要监控的公众号。
4. 执行 `wechat-reader weekly-update --days N` 获取近期文章链接。
5. 程序提取文章正文并生成摘要。
6. 数据写入 `frontend/api/articles.json`、`accounts.json` 和 `monitors.json`。
7. 执行 `wechat-reader export --sync` 可将静态前端同步到 GitHub。

## 快速开始

如果你想按最短路径跑通一次，请阅读 [QUICKSTART.md](QUICKSTART.md)。

基础流程如下：

```bash
git clone https://github.com/yourusername/wechat-article-viewer.git
cd wechat-article-viewer

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

如果命令提示需要登录，请在普通终端里运行更新命令，并按提示完成微信扫码登录。

## 配合 AI Agent 使用

如果你希望让 AI 编程 Agent 操作这个项目，请先让它阅读 [AGENTS.md](AGENTS.md)。

推荐提示词：

```text
请先阅读 README.md、AGENTS.md、QUICKSTART.md 和 TROUBLESHOOTING.md。
请帮我在本地配置这个微信公众号文章阅读器，添加我要监控的公众号，
运行一次更新测试，并安装每天 10:00 执行的本地定时任务。
不要提交 .env、config.json、data/session.json、logs、backups 或本地运行文件。
```

## 常用命令

```bash
# 初始化目录和配置
wechat-reader init

# 配置 LLM 参数
wechat-reader config set llm_api_key "your-api-key"
wechat-reader config set llm_model "minimax/minimax-m2.5:free"
wechat-reader config set llm_base_url "https://openrouter.ai/api/v1"

# 管理监控公众号
wechat-reader monitor add "公众号名称"
wechat-reader monitor list
wechat-reader monitor remove "公众号名称"

# 采集单个公众号或单篇文章
wechat-reader collect account "公众号名称" --recent 7
wechat-reader collect article "https://mp.weixin.qq.com/s/..."

# 更新所有已监控公众号
wechat-reader weekly-update --days 2

# 将静态前端同步到 Git
wechat-reader export --sync
```

## 每日自动化

推荐使用本地自动化。微信公众号文章采集依赖本地登录状态，因此本地计划任务通常比纯云端任务更稳定。

项目提供了可复用模板：

- `scripts/daily_update.example.sh`
- `launchd/com.wechat-reader.daily-update.plist.template`

macOS 典型配置：

```bash
cp scripts/daily_update.example.sh scripts/daily_update.sh
chmod +x scripts/daily_update.sh
```

替换 `scripts/daily_update.sh` 里的占位符：

```text
__PROJECT_DIR__  项目绝对路径
__PYTHON_BIN__   Python 解释器路径，例如 /path/to/.venv/bin/python
__DAYS__         推荐值：2
```

然后复制并填写 launchd 模板：

```bash
cp launchd/com.wechat-reader.daily-update.plist.template \
  "$HOME/Library/LaunchAgents/com.wechat-reader.daily-update.plist"
```

替换占位符：

```text
__PROJECT_DIR__  项目绝对路径
__HOUR__         10
__MINUTE__       0
```

加载定时任务：

```bash
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.wechat-reader.daily-update.plist"
launchctl enable "gui/$(id -u)/com.wechat-reader.daily-update"
```

查看状态：

```bash
launchctl print "gui/$(id -u)/com.wechat-reader.daily-update"
```

查看日志：

```bash
tail -f logs/daily-update.log
tail -f logs/daily-update.err.log
```

## 发布网站

前端是位于 `frontend` 的静态网站。

Cloudflare Pages 推荐配置：

- 构建命令：`echo "No build needed"`
- 构建输出目录：`frontend`

`wechat-reader export --sync` 会使用 Git 发布前端。启用前请先确认你的仓库结构，因为当前实现采用基于 `frontend` 目录的 subtree 推送方式。

## 配置说明

可以使用 `config.json` 或环境变量。

复制配置示例：

```bash
cp config/config.json.example config.json
```

重要路径规则：

```json
{
  "frontend_dir": "frontend"
}
```

程序内部会自动追加 `/api`，所以数据实际写入 `frontend/api`。

对应的环境变量写法：

```bash
WECHAT_READER_FRONTEND_DIR=frontend
```

支持 OpenAI 兼容接口，包括 OpenRouter、OpenAI、豆包、通义千问兼容网关，以及其他兼容服务。

## 安全提示

不要提交：

- `.env`
- `config.json`
- `data/session.json`
- `logs/`
- `backups/`
- 包含本机私有路径的本地 launchd 文件

项目的 `.gitignore` 已排除常见本地运行文件，但提交或推送前仍应检查 `git status`。

## 故障排查

常见问题请阅读 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)：

- 微信登录状态过期。
- 没有采集到文章。
- 文章正文解析失败。
- LLM 摘要生成失败。
- GitHub 推送失败。
- launchd 没有运行。

## 项目结构

```text
wechat-article-viewer/
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

## 许可证

MIT License

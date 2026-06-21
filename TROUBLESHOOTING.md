# 故障排查

当更新、定时任务、登录、摘要生成或发布步骤失败时，请参考这份指南。

## 先做基础检查

请在仓库根目录执行命令。

```bash
pwd
wechat-reader --help
wechat-reader config list
wechat-reader monitor list
```

如果没有安装包，而是直接从源码运行：

```bash
PYTHONPATH=src python3 -m wechat_reader --help
```

## 微信登录状态过期

典型现象：

- 更新命令要求重新登录。
- Session 校验失败。
- 请求微信公众号平台时返回登录页或权限页。

处理方式：

```bash
wechat-reader weekly-update --days 1
```

如果命令提示扫码登录，请按流程完成二维码登录。Session 会保存在本地 `data/` 目录下，不能提交到 Git。

如果是 AI Agent 正在操作项目，它应当停止自动流程，并请求用户手动完成登录。

定时任务建议使用 `weekly-update --no-login`。这样 session 无效时任务会直接退出并写日志，不会在无人值守环境中打开浏览器等待扫码。

## LLM API Key 或模型配置失败

典型现象：

- 已找到文章链接，但摘要生成失败。
- 日志中出现 API Key、认证、模型、额度或 Base URL 相关错误。

检查配置：

```bash
wechat-reader config get llm_api_key
wechat-reader config get llm_model
wechat-reader config get llm_base_url
```

重新设置：

```bash
wechat-reader config set llm_api_key "your-api-key"
wechat-reader config set llm_model "minimax/minimax-m2.5:free"
wechat-reader config set llm_base_url "https://openrouter.ai/api/v1"
```

如果使用 `.env`，请重新加载：

```bash
set -a
source .env
set +a
```

## 没有采集到文章

典型现象：

- `weekly-update` 检查了公众号，但没有新增文章。
- 日志频繁提示文章时间早于阈值。

可能原因：

- 被监控公众号在指定时间窗口内没有发文。
- 文章此前已经采集过，并按链接去重。
- 更新时间窗口太窄，跨天边界附近容易漏抓。
- 公众号 fakeid 错误或已过期。

建议尝试：

```bash
wechat-reader weekly-update --days 2
```

然后检查 `frontend/api/articles.json` 和日志。

## 文章正文解析失败

典型现象：

- 日志包含 `未找到文章内容区域`。
- 日志包含 `提取内容失败`。
- 候选文章已找到，但没有被加入文章库。

常见原因：

- 文章没有普通文本正文。
- 文章已删除、受限，或主要由图片/视频组成。
- 微信返回了验证页、跳转页或非标准页面。
- 文章模板中没有预期的 `#js_content` 区域。

这通常是局部失败。同一次更新里的其他文章仍然可能成功。

如有需要，请手动在浏览器里打开失败链接，确认是否存在可读正文。

## GitHub 推送或静态发布失败

典型现象：

- `wechat-reader export --sync` 失败。
- Git 要求输入凭据。
- Cloudflare Pages 没有更新。

检查 Git：

```bash
git status
git remote -v
git branch --show-current
```

检查前端数据是否变化：

```bash
git diff -- frontend/api/articles.json frontend/api/accounts.json frontend/api/monitors.json
```

重新同步：

```bash
wechat-reader export --sync
```

Cloudflare Pages 请确认：

- 构建命令：`echo "No build needed"`
- 构建输出目录：`frontend`
- 连接分支与你的发布策略一致。

## launchd 没有运行

典型现象：

- 每日更新没有发生。
- 没有写入日志。
- `launchctl print` 显示错误。

检查 plist：

```bash
plutil -lint "$HOME/Library/LaunchAgents/com.wechat-reader.daily-update.plist"
```

检查状态：

```bash
launchctl print "gui/$(id -u)/com.wechat-reader.daily-update"
```

手动运行一次：

```bash
launchctl kickstart -k "gui/$(id -u)/com.wechat-reader.daily-update"
```

查看日志：

```bash
tail -f logs/daily-update.log
tail -f logs/daily-update.err.log
```

在 macOS 上，如果 launchd 报 `Operation not permitted`，请避免直接从受隐私保护的目录运行定时任务。可以把运行副本移动到普通用户目录，并更新 `__PROJECT_DIR__`。

## 定时任务找不到 PATH 或 Python

典型现象：

- 手动更新成功。
- 定时更新失败，并出现 `python: command not found` 或模块导入错误。

请在 `scripts/daily_update.sh` 中使用 Python 的绝对路径：

```bash
which python
```

然后设置：

```bash
PYTHON_BIN="/absolute/path/to/python"
```

如果直接从源码运行，请保留：

```bash
export PYTHONPATH="$PROJECT_DIR/src"
```

## 安全重跑

更新任务可以安全重跑，因为文章会按链接去重。

```bash
wechat-reader weekly-update --days 2
wechat-reader export --sync
```

除非用户明确希望重建数据集，否则不要为了修复一次失败运行而删除 `frontend/api/articles.json`。

## 应保留在本地的文件

不要提交：

- `.env`
- `config.json`
- `data/`
- `logs/`
- `backups/`
- `.daily-update.lock/`

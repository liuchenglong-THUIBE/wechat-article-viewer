# 快速开始

这份指南用于帮助你从一个全新的 clone 开始，完成一次本地更新测试。

## 1. 克隆项目

```bash
git clone https://github.com/yourusername/wechat-article-viewer.git
cd wechat-article-viewer
```

## 2. 创建 Python 环境

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
playwright install chromium
```

## 3. 配置项目

请选择一种配置方式。

### 方式 A：使用环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```dotenv
WECHAT_READER_LLM_API_KEY=your-api-key-here
WECHAT_READER_LLM_MODEL=minimax/minimax-m2.5:free
WECHAT_READER_LLM_BASE_URL=https://openrouter.ai/api/v1
WECHAT_READER_FRONTEND_DIR=frontend
```

在当前 shell 中加载：

```bash
set -a
source .env
set +a
```

### 方式 B：使用 config.json

```bash
cp config/config.json.example config.json
wechat-reader config set llm_api_key "your-api-key"
```

重要配置：

```json
{
  "frontend_dir": "frontend"
}
```

程序会把 API 数据写入 `frontend/api`。

## 4. 初始化

```bash
wechat-reader init
```

这个命令会创建前端 API 数据目录，并写入默认本地配置。

## 5. 添加公众号

```bash
wechat-reader monitor add "晚点LatePost"
wechat-reader monitor add "腾讯研究院"
wechat-reader monitor list
```

## 6. 执行一次更新

```bash
wechat-reader weekly-update --days 2
```

如果需要微信登录，请按工具显示的二维码登录流程操作。登录状态会保存在本地，不应提交到 Git。

## 7. 检查数据

```bash
ls frontend/api
```

预期文件：

```text
accounts.json
articles.json
monitors.json
```

## 8. 发布静态网站

如果你的 GitHub 仓库和静态托管服务已经配置好：

```bash
wechat-reader export --sync
```

Cloudflare Pages 推荐配置：

- 构建命令：`echo "No build needed"`
- 构建输出目录：`frontend`

## 9. 可选：每日定时任务

复制可复用脚本模板：

```bash
cp scripts/daily_update.example.sh scripts/daily_update.sh
chmod +x scripts/daily_update.sh
```

替换：

```text
__PROJECT_DIR__  本仓库的绝对路径
__PYTHON_BIN__   .venv/bin/python 的绝对路径
__DAYS__         2
```

复制 launchd 模板：

```bash
cp launchd/com.wechat-reader.daily-update.plist.template \
  "$HOME/Library/LaunchAgents/com.wechat-reader.daily-update.plist"
```

替换：

```text
__PROJECT_DIR__  本仓库的绝对路径
__HOUR__         10
__MINUTE__       0
```

加载定时任务：

```bash
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.wechat-reader.daily-update.plist"
launchctl enable "gui/$(id -u)/com.wechat-reader.daily-update"
```

手动测试一次：

```bash
launchctl kickstart -k "gui/$(id -u)/com.wechat-reader.daily-update"
```

查看日志：

```bash
tail -f logs/daily-update.log
tail -f logs/daily-update.err.log
```

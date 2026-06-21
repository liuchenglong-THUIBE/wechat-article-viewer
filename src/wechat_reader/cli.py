"""
命令行界面

使用 Click 构建的 CLI 工具
"""

import sys
from pathlib import Path

import click

from .core.config import Config
from .core.reader import WechatReader


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="配置文件路径",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="显示详细日志",
)
@click.pass_context
def cli(ctx: click.Context, config: str | None, verbose: bool) -> None:
    """
    微信公众号阅读器

    采集公众号文章，生成 AI 摘要，导出到静态网站
    """
    # 确保上下文对象存在
    ctx.ensure_object(dict)

    # 加载配置
    ctx.obj["config"] = Config(config_path=config)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """初始化应用"""
    config = ctx.obj["config"]

    click.echo("🚀 初始化微信公众号阅读器...")

    # 创建必要目录
    config.get_frontend_api_dir().mkdir(parents=True, exist_ok=True)

    # 保存默认配置
    config.save()

    click.echo(f"✅ 配置已保存到: {config.config_path}")
    click.echo(f"✅ 数据目录: {config.get_frontend_api_dir()}")
    click.echo("")
    click.echo("💡 下一步:")
    click.echo("  1. 配置 LLM API Key: wechat-reader config set llm_api_key <your-key>")
    click.echo("  2. 开始采集: wechat-reader collect account <公众号名称>")


@cli.group()
def collect() -> None:
    """采集文章"""
    pass


@collect.command(name="account")
@click.argument("name")
@click.option(
    "--recent",
    "-r",
    type=int,
    default=7,
    help="只采集最近N天的文章，默认7天",
)
@click.pass_context
def collect_account(ctx: click.Context, name: str, recent: int) -> None:
    """采集公众号文章（使用两阶段优化采集）"""
    config = ctx.obj["config"]
    reader = WechatReader(config=config)

    click.echo(f"🕷️ 正在采集公众号: {name}")
    click.echo(f"   只采集最近 {recent} 天的文章")
    result = reader.collect_account_recent(name, days=recent)

    if result.get("success", True):
        click.echo(f"✅ 采集完成")
        click.echo(f"   文章数: {result.get('total_articles', 0)}")
        click.echo(f"   新增: {result.get('new_articles', 0)}")
    else:
        click.echo(f"❌ 采集失败: {result.get('message', '未知错误')}")
        sys.exit(1)


@collect.command(name="article")
@click.argument("url")
@click.pass_context
def collect_article(ctx: click.Context, url: str) -> None:
    """采集单篇文章"""
    config = ctx.obj["config"]
    reader = WechatReader(config=config)

    click.echo(f"🕷️ 正在采集文章: {url}")

    result = reader.collect_article(url)

    if result.get("success"):
        click.echo(f"✅ 采集成功")
    else:
        click.echo(f"❌ 采集失败: {result.get('message', '未知错误')}")
        sys.exit(1)


@cli.group()
def monitor() -> None:
    """管理监控列表"""
    pass


@monitor.command(name="add")
@click.argument("account_name")
@click.pass_context
def monitor_add(ctx: click.Context, account_name: str) -> None:
    """添加公众号到监控列表"""
    config = ctx.obj["config"]
    reader = WechatReader(config=config)

    if reader.add_monitor(account_name):
        click.echo(f"✅ 已添加 '{account_name}' 到监控列表")
    else:
        click.echo(f"❌ 添加失败")
        sys.exit(1)


@monitor.command(name="remove")
@click.argument("account_name")
@click.pass_context
def monitor_remove(ctx: click.Context, account_name: str) -> None:
    """从监控列表移除公众号"""
    config = ctx.obj["config"]
    reader = WechatReader(config=config)

    if reader.remove_monitor(account_name):
        click.echo(f"✅ 已移除 '{account_name}'")
    else:
        click.echo(f"⚠️ '{account_name}' 不在监控列表中")


@monitor.command(name="list")
@click.pass_context
def monitor_list(ctx: click.Context) -> None:
    """列出监控列表"""
    config = ctx.obj["config"]
    reader = WechatReader(config=config)

    monitors = reader.list_monitors()

    if not monitors:
        click.echo("📋 监控列表为空")
        return

    click.echo(f"📋 监控列表（共 {len(monitors)} 个）:")
    for i, m in enumerate(monitors, 1):
        click.echo(f"  {i}. {m['account_name']}")


@cli.command()
@click.option(
    "--days",
    "-d",
    type=int,
    default=7,
    help="获取最近几天的文章，默认7天",
)
@click.option(
    "--no-login",
    is_flag=True,
    help="禁止自动打开浏览器登录；session 无效时直接退出",
)
@click.pass_context
def weekly_update(ctx: click.Context, days: int, no_login: bool) -> None:
    """执行每周更新（使用两阶段优化采集：先快速获取链接，再并发生成摘要）"""
    config = ctx.obj["config"]
    reader = WechatReader(config=config)

    click.echo(f"[开始] 每周更新（两阶段+10并发），获取最近 {days} 天的文章...")
    result = reader.optimized_weekly_update(days=days, allow_browser_login=not no_login)

    if result.get("success"):
        click.echo(f"[成功] {result.get('message')}")
        click.echo(f"   阶段1（获取链接）耗时: {result.get('stage1_time', 'N/A')}")
        click.echo(f"   阶段2（生成摘要）耗时: {result.get('stage2_time', 'N/A')}")
    else:
        click.echo(f"[失败] 更新失败: {result.get('message')}")
        sys.exit(1)


@cli.command()
@click.option(
    "--sync",
    "-s",
    is_flag=True,
    help="同步到 Git",
)
@click.pass_context
def export(ctx: click.Context, sync: bool) -> None:
    """导出数据到前端目录并可选同步到 Git"""
    config = ctx.obj["config"]
    reader = WechatReader(config=config)

    click.echo("📤 数据已保存在 frontend/api/ 目录")

    if sync:
        click.echo("")
        click.echo("🔄 正在同步到 Git...")
        sync_result = reader.sync_git()
        if sync_result.get("success"):
            click.echo(f"✅ {sync_result.get('message')}")
        else:
            click.echo(f"⚠️ {sync_result.get('message')}")


@cli.group()
def config_cmd() -> None:
    """配置管理"""
    pass


@config_cmd.command(name="get")
@click.argument("key")
@click.pass_context
def config_get(ctx: click.Context, key: str) -> None:
    """获取配置项"""
    config = ctx.obj["config"]
    value = config.get(key)

    if key == "llm_api_key" and value:
        # 隐藏 API Key
        value = value[:8] + "..." + value[-4:]

    click.echo(f"{key}: {value}")


@config_cmd.command(name="set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """设置配置项"""
    config = ctx.obj["config"]

    # 类型转换
    if value.lower() in ("true", "yes", "1"):
        value = True
    elif value.lower() in ("false", "no", "0"):
        value = False
    elif value.isdigit():
        value = int(value)

    config.set(key, value)
    config.save()

    click.echo(f"✅ 已设置 {key} = {value}")


@config_cmd.command(name="list")
@click.pass_context
def config_list(ctx: click.Context) -> None:
    """列出所有配置"""
    config = ctx.obj["config"]

    click.echo("📋 当前配置:")
    for key, value in config.to_dict().items():
        if key == "llm_api_key" and value:
            # 隐藏 API Key
            value = value[:8] + "..." + value[-4:]
        click.echo(f"  {key}: {value}")


def main() -> None:
    """入口函数"""
    cli()


if __name__ == "__main__":
    main()

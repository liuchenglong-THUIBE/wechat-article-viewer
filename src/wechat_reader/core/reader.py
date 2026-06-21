"""
微信公众号阅读器核心类
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

from ..browser.wechat_authenticator import WechatAuthenticator
from ..llm import create_llm_provider
from ..llm.base import LLMProvider
from ..services.search_service import SearchService
from ..services.wechat_service import WechatService
from ..utils.logger import get_module_logger
from .config import Config
from .json_storage import get_storage

logger = get_module_logger(__name__)


class WechatReader:
    """
    微信公众号阅读器

    主要功能：
    - 采集公众号文章
    - 生成文章摘要
    - 同步到 Git
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        """
        初始化阅读器

        Args:
            config: 配置对象，默认创建新实例
            llm_provider: LLM 提供者，默认根据配置创建
        """
        self.config = config or Config()

        # 初始化 JSON 存储
        self.storage = get_storage(self.config.get_frontend_api_dir())

        # 初始化 LLM
        if llm_provider:
            self.llm = llm_provider
        else:
            self.llm = create_llm_provider()

        # 初始化服务
        self.wechat_auth = WechatAuthenticator()
        self.search_service = SearchService()
        self.wechat_service = WechatService(self.storage)

    def collect_article(self, url: str) -> dict[str, Any]:
        """
        采集单篇文章

        Args:
            url: 文章链接

        Returns:
            采集结果
        """
        try:
            logger.info(f"开始采集单篇文章: {url}")

            # 1. 确保已认证
            if not self.wechat_auth.ensure_authenticated():
                return {
                    "success": False,
                    "message": "微信认证失败",
                }

            # 2. 检查文章是否已存在
            existing = self.storage.get_article_by_link(url)
            if existing:
                logger.info(f"文章已存在: {url}")
                return {
                    "success": True,
                    "message": "文章已存在",
                    "summary": existing.get("article_summary", ""),
                }

            # 3. 提取文章内容
            success, content, html_publish_time, html_title = self.wechat_auth.get_article_content_from_url(url)
            if not success:
                return {
                    "success": False,
                    "message": "提取文章内容失败",
                }

            # 4. 生成摘要
            summary = self.llm.generate_summary(html_title or "文章", content)

            # 5. 保存到 JSON
            article = self.storage.add_article({
                "account_name": "单篇采集",
                "article_title": html_title or "未知标题",
                "article_link": url,
                "article_summary": summary,
                "publish_time": html_publish_time,
            })

            logger.info(f"文章采集成功: {url}")

            return {
                "success": True,
                "message": "文章采集成功",
                "summary": summary,
                "article_id": article.get("id"),
            }

        except Exception as e:
            logger.error(f"采集文章失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"采集失败: {str(e)}",
            }

    def _fetch_account_articles(
        self, fakeid: str, session_data: dict[str, Any],
        since_timestamp: int = 0, max_pages: int = 10
    ) -> list[dict[str, Any]]:
        """
        获取公众号文章列表（支持翻页和时间过滤）

        Args:
            fakeid: 公众号的 fakeid
            session_data: 认证会话数据
            since_timestamp: 只获取此时间戳之后的文章（0表示获取所有）
            max_pages: 最大翻页次数

        Returns:
            文章列表
        """
        import requests

        articles = []
        begin = 0
        count = 20
        page = 1

        try:
            token = session_data.get("token", "")

            # 构建cookies
            cookie_list = session_data.get("cookies", [])
            cookies = {}
            for cookie in cookie_list:
                if cookie.get("name") and cookie.get("value") is not None:
                    cookies[cookie["name"]] = cookie["value"]

            # 构建请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": f"https://mp.weixin.qq.com/cgi-bin/appmsg?token={token}&lang=zh_CN&type=10&action=list_ex&begin=0&count=20",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

            logger.info(f"获取文章列表，fakeid: {fakeid[:20]}...")

            while page <= max_pages:
                # 构建请求URL - 使用 appmsgpublish API
                url = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"
                params = {
                    "sub": "list",
                    "search_field": "null",
                    "begin": begin,
                    "count": count,
                    "query": "",
                    "fakeid": fakeid,
                    "type": "101_1",
                    "free_publish_type": "1",
                    "sub_action": "list_ex",
                    "token": token,
                    "lang": "zh_CN",
                    "f": "json",
                    "ajax": "1",
                }

                logger.info(f"获取第 {page} 页文章，begin={begin}...")

                response = requests.get(
                    url,
                    params=params,
                    cookies=cookies,
                    headers=headers,
                    timeout=30
                )

                result = response.json()

                if result.get("base_resp", {}).get("ret") != 0:
                    error_msg = result.get("base_resp", {}).get("err_msg", "未知错误")
                    logger.error(f"获取文章列表失败: {error_msg}")
                    break

                # 解析 publish_page JSON字符串
                import json
                publish_page = json.loads(result.get("publish_page", "{}"))
                publish_list = publish_page.get("publish_list", [])

                if not publish_list:
                    logger.info(f"第 {page} 页没有文章，结束翻页")
                    break

                page_articles = 0
                for item in publish_list:
                    publish_info = json.loads(item.get("publish_info", "{}"))
                    appmsgex_list = publish_info.get("appmsgex", [])

                    # 尝试从 item 获取推送时间作为回退
                    push_time = item.get("publish_time") or item.get("update_time") or item.get("create_time") or 0
                    if not push_time:
                        push_time = publish_info.get("update_time") or publish_info.get("create_time") or 0

                    for appmsg in appmsgex_list:
                        # 优先使用 update_time（通常代表实际发布或更新时间），如果没有则使用 create_time，再没有则使用 push_time
                        create_time = appmsg.get("update_time") or appmsg.get("create_time") or push_time or 0

                        # 如果时间过滤，跳过旧文章
                        if since_timestamp > 0 and create_time < since_timestamp:
                            logger.info(f"文章时间早于阈值，停止翻页")
                            return articles

                        article_info = {
                            "title": appmsg.get("title", ""),
                            "link": appmsg.get("link", ""),
                            "create_time": create_time,
                        }
                        if article_info["link"]:
                            articles.append(article_info)
                            page_articles += 1

                logger.info(f"第 {page} 页获取 {page_articles} 篇文章，累计 {len(articles)} 篇")

                # 如果本页文章数少于count，说明没有更多文章了
                if page_articles < count:
                    logger.info("本页文章不足，结束翻页")
                    break

                # 翻页
                begin += count
                page += 1

                # 添加延时避免频率限制
                if page <= max_pages:
                    time.sleep(1)

        except Exception as e:
            logger.error(f"获取文章列表异常: {e}", exc_info=True)

        logger.info(f"总共获取 {len(articles)} 篇文章")
        return articles

    def add_monitor(self, account_name: str) -> bool:
        """
        添加公众号到监控列表

        Args:
            account_name: 公众号名称

        Returns:
            是否成功
        """
        try:
            # 如果本地有 fakeid，则顺便把 fakeid 也加上
            selected_account = self.storage.get_account_by_name(account_name)
            fakeid = selected_account.get("fakeid", "") if selected_account else ""
            self.storage.add_monitor(account_name, fakeid)
            return True
        except Exception as e:
            logger.error(f"添加监控失败: {e}")
            return False

    def remove_monitor(self, account_name: str) -> bool:
        """
        从监控列表移除公众号

        Args:
            account_name: 公众号名称

        Returns:
            是否成功
        """
        try:
            return self.storage.remove_monitor(account_name)
        except Exception as e:
            logger.error(f"移除监控失败: {e}")
            return False

    def list_monitors(self) -> list[dict]:
        """
        列出监控列表

        Returns:
            监控列表
        """
        return self.storage.get_all_monitors()

    def collect_account_recent(
        self, account_name: str, days: int = 7
    ) -> dict[str, Any]:
        """
        采集公众号最近几天的文章（用于每周更新）

        Args:
            account_name: 公众号名称
            days: 获取最近几天的文章，默认7天

        Returns:
            采集结果统计
        """
        from datetime import datetime, timedelta

        try:
            logger.info(f"开始采集公众号最近{days}天文章: {account_name}")

            # 1. 确保已认证
            if not self.wechat_auth.ensure_authenticated():
                return {
                    "success": False,
                    "message": "微信认证失败",
                    "total_articles": 0,
                }

            # 2. 获取会话
            session_data = self.wechat_auth.get_session_data()
            if not session_data:
                return {
                    "success": False,
                    "message": "获取会话失败",
                    "total_articles": 0,
                }

            # 3. 搜索公众号
            logger.info(f"搜索公众号: {account_name}")
            search_results = self.search_service.search_public_accounts(
                account_name, session_data
            )

            if not search_results:
                return {
                    "success": False,
                    "message": f"未找到公众号: {account_name}",
                    "total_articles": 0,
                }

            # 4. 选择第一个匹配的公众号
            selected_account = search_results[0]
            logger.info(f"选中公众号: {selected_account['nickname']}")

            # 5. 保存到 JSON
            self.storage.add_account({
                "account_name": selected_account["nickname"],
                "fakeid": selected_account["fakeid"],
                "description": selected_account.get("signature", ""),
            })

            # 6. 计算时间阈值（只获取最近几天的文章）
            since_date = datetime.now() - timedelta(days=days)
            since_timestamp = int(since_date.timestamp())
            logger.info(f"只获取 {since_date.strftime('%Y-%m-%d')} 之后的文章")

            # 7. 采集文章（带时间过滤，只翻页到时间阈值为止）
            logger.info(f"开始采集文章，公众号: {selected_account['nickname']}")

            articles = self._fetch_account_articles(
                selected_account["fakeid"],
                session_data,
                since_timestamp=since_timestamp,
                max_pages=20
            )

            logger.info(f"获取到 {len(articles)} 篇最近文章")

            # 8. 处理文章
            new_articles = 0

            for article_info in articles:
                # 检查文章是否已存在
                if not self.storage.article_exists(article_info["link"]):
                    # 提取文章内容
                    success, content, html_publish_time, html_title = self.wechat_auth.get_article_content_from_url(
                        article_info["link"]
                    )

                    if success and content:
                        # 生成摘要
                        summary = self.llm.generate_summary(
                            article_info["title"],
                            content
                        )

                        # 确定最终发布时间 (优先使用HTML解析出的时间)
                        final_publish_time = html_publish_time
                        if not final_publish_time and article_info.get("create_time"):
                            final_publish_time = datetime.fromtimestamp(article_info["create_time"]).isoformat()

                        # 保存文章
                        self.storage.add_article({
                            "account_name": selected_account["nickname"],
                            "article_title": article_info["title"] or html_title,
                            "article_link": article_info["link"],
                            "article_summary": summary,
                            "publish_time": final_publish_time,
                        })
                        new_articles += 1

                        logger.info(f"新增文章: {article_info['title']}")

            logger.info(f"成功采集 {new_articles} 篇新文章")

            return {
                "success": True,
                "message": f"成功添加公众号: {selected_account['nickname']}",
                "account_name": selected_account["nickname"],
                "total_articles": len(articles),
                "new_articles": new_articles,
            }

        except Exception as e:
            logger.error(f"采集公众号失败: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"采集失败: {str(e)}",
                "total_articles": 0,
            }

    def batch_collect_article_links(
        self,
        days: int = 7,
        allow_browser_login: bool = True,
    ) -> dict[str, Any]:
        """
        第一阶段：批量快速获取所有公众号的文章链接（不提取内容）

        这个阶段只使用API获取文章列表，速度极快，不需要浏览器提取内容

        Args:
            days: 获取最近几天的文章

        Returns:
            采集结果，包含所有获取到的文章链接
        """
        from datetime import datetime, timedelta

        monitors = self.list_monitors()
        if not monitors:
            return {"success": True, "message": "监控列表为空", "articles": []}

        logger.info(f"[阶段1] 批量获取文章链接，共 {len(monitors)} 个公众号，最近 {days} 天")

        # 1. 确保已认证（只认证一次）
        if not self.wechat_auth.ensure_authenticated(allow_browser_login=allow_browser_login):
            return {
                "success": False,
                "message": "微信认证失败：已有 session 无效或无法验证，请手动登录后重试",
                "articles": [],
            }

        session_data = self.wechat_auth.get_session_data()
        if not session_data:
            return {"success": False, "message": "获取会话失败", "articles": []}

        since_date = datetime.now() - timedelta(days=days)
        since_timestamp = int(since_date.timestamp())

        all_articles = []
        processed_accounts = 0

        # 2. 快速获取所有公众号的文章列表
        for monitor in monitors:
            account_name = monitor["account_name"]
            try:
                logger.info(f"[{processed_accounts + 1}/{len(monitors)}] 获取文章列表: {account_name}")

                # 优先从本地 accounts.json 中获取 fakeid，避免被搜索接口限流
                selected_account = self.storage.get_account_by_name(account_name)

                # 如果没有 fakeid，或者 fakeid 是像 "1" 这样的假数字（小于 10 位），则重新搜索获取真实 fakeid
                if not selected_account or not selected_account.get("fakeid") or (str(selected_account.get("fakeid")).isdigit() and len(str(selected_account.get("fakeid"))) < 10):
                    # 搜索公众号
                    search_results = self.search_service.search_public_accounts(account_name, session_data)
                    if not search_results:
                        logger.warning(f"未找到公众号: {account_name}")
                        continue

                    search_selected = search_results[0]

                    # 补充保存公众号信息 (如果存在则会更新)
                    if selected_account and "id" in selected_account:
                        self.storage.update_account(selected_account["id"], {
                            "fakeid": search_selected["fakeid"],
                            "description": search_selected.get("signature", ""),
                        })
                    else:
                        self.storage.add_account({
                            "account_name": search_selected["nickname"],
                            "fakeid": search_selected["fakeid"],
                            "description": search_selected.get("signature", ""),
                        })

                    selected_account = {
                        "nickname": search_selected["nickname"],
                        "fakeid": search_selected["fakeid"],
                    }
                else:
                    # 适配返回的数据结构
                    selected_account["nickname"] = selected_account.get("account_name", "")

                # 获取文章列表（只调用API，不提取内容）
                articles = self._fetch_account_articles(
                    selected_account["fakeid"],
                    session_data,
                    since_timestamp=since_timestamp,
                    max_pages=20
                )

                # 检查哪些文章是新的
                for article_info in articles:
                    if not self.storage.article_exists(article_info["link"]):
                        article_data = {
                            "account_name": selected_account["nickname"],
                            "title": article_info["title"],
                            "link": article_info["link"],
                            "create_time": article_info.get("create_time"),
                        }
                        all_articles.append(article_data)

                processed_accounts += 1

                # 添加小延时避免频率限制
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"获取 {account_name} 文章列表失败: {e}")
                continue

        logger.info(f"[阶段1完成] 共获取 {len(all_articles)} 篇新文章链接")

        return {
            "success": True,
            "message": f"获取了 {len(all_articles)} 篇新文章链接",
            "articles": all_articles,
            "total_accounts": len(monitors),
            "processed_accounts": processed_accounts,
        }

    def batch_generate_summaries(self, articles: list[dict], max_workers: int = 10) -> dict[str, Any]:
        """
        第二阶段：批量生成文章摘要（并发处理）

        使用线程池并发处理文章，大幅提升速度

        Args:
            articles: 文章列表，包含account_name, title, link, create_time
            max_workers: 并发线程数，默认10

        Returns:
            处理结果统计
        """
        from datetime import datetime
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading

        if not articles:
            return {"success": True, "message": "没有需要处理的文章", "processed": 0}

        logger.info(f"[阶段2] 批量生成摘要，共 {len(articles)} 篇文章，并发数: {max_workers}")

        processed = 0
        failed = 0
        lock = threading.Lock()

        def process_article(article_data: dict, index: int) -> dict:
            """处理单篇文章"""
            nonlocal processed, failed

            logger.info(f"[{index}/{len(articles)}] 开始处理: {article_data['title'][:40]}...")

            try:
                # 提取文章内容
                success, content, html_publish_time, html_title = self.wechat_auth.get_article_content_from_url(
                    article_data["link"]
                )

                if not success or not content:
                    logger.warning(f"  [{index}] 提取内容失败")
                    with lock:
                        failed += 1
                    return {"success": False, "index": index}

                # 生成摘要
                summary = self.llm.generate_summary(
                    article_data["title"] or html_title or "文章",
                    content
                )

                # 确定最终发布时间 (优先使用HTML解析出的时间)
                final_publish_time = html_publish_time
                if not final_publish_time and article_data.get("create_time"):
                    final_publish_time = datetime.fromtimestamp(article_data["create_time"]).isoformat()

                # 保存到 JSON
                self.storage.add_article({
                    "account_name": article_data["account_name"],
                    "article_title": article_data["title"] or html_title or "未知标题",
                    "article_link": article_data["link"],
                    "article_summary": summary,
                    "publish_time": final_publish_time,
                })

                with lock:
                    processed += 1
                logger.info(f"  [{index}] 成功完成")
                return {"success": True, "index": index}

            except Exception as e:
                logger.error(f"[{index}] 处理异常: {e}")
                with lock:
                    failed += 1
                return {"success": False, "index": index, "error": str(e)}

        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(process_article, article, i+1): i+1
                for i, article in enumerate(articles)
            }

            for future in as_completed(future_to_index):
                try:
                    result = future.result()
                except Exception as e:
                    logger.error(f"任务执行异常: {e}")
                    with lock:
                        failed += 1

        logger.info(f"[阶段2完成] 成功: {processed}, 失败: {failed}")

        return {
            "success": True,
            "message": f"处理了 {len(articles)} 篇文章，成功 {processed} 篇，失败 {failed} 篇",
            "processed": processed,
            "failed": failed,
        }

    def optimized_weekly_update(
        self,
        days: int = 7,
        allow_browser_login: bool = True,
    ) -> dict[str, Any]:
        """
        优化的每周更新（两阶段处理）

        阶段1：快速获取所有文章链接（API调用，速度快）
        阶段2：批量生成摘要（并发处理，默认10线程）

        Args:
            days: 获取最近几天的文章
            allow_browser_login: session 不可用时是否允许打开浏览器扫码登录

        Returns:
            更新结果统计
        """
        logger.info(f"=== 开始优化的每周更新（最近 {days} 天）===")

        # 阶段1：快速获取文章链接
        start_time = time.time()
        stage1_result = self.batch_collect_article_links(
            days,
            allow_browser_login=allow_browser_login,
        )
        stage1_time = time.time() - start_time

        if not stage1_result.get("success"):
            return stage1_result

        articles = stage1_result.get("articles", [])

        # 阶段2：批量生成摘要（并发处理）
        if articles:
            start_time = time.time()
            stage2_result = self.batch_generate_summaries(articles)
            stage2_time = time.time() - start_time

            return {
                "success": True,
                "message": f"更新完成：获取 {len(articles)} 篇文章，成功处理 {stage2_result.get('processed', 0)} 篇",
                "stage1_time": f"{stage1_time:.1f}秒",
                "stage2_time": f"{stage2_time:.1f}秒",
                "total_new": stage2_result.get("processed", 0),
            }
        else:
            return {
                "success": True,
                "message": "没有发现新文章",
                "stage1_time": f"{stage1_time:.1f}秒",
                "total_new": 0,
            }

    def sync_git(self) -> dict[str, Any]:
        """
        同步 frontend 目录到 Git
        使用 git subtree 只推送 frontend 目录到远程仓库

        Returns:
            同步结果
        """
        if not self.config.get("auto_git_push", True):
            return {
                "success": True,
                "message": "自动 Git Push 已关闭",
            }

        try:
            project_root = Path(__file__).parent.parent.parent.parent

            # 检查是否是 git 仓库
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": "当前目录不是 Git 仓库",
                }

            # 添加 frontend 目录的变更
            frontend_dir = project_root / "frontend"
            subprocess.run(
                ["git", "add", str(frontend_dir)],
                cwd=project_root,
                check=True,
            )

            # 提交变更
            try:
                subprocess.run(
                    ["git", "commit", "-m", "auto: update articles"],
                    cwd=project_root,
                    check=True,
                )
            except subprocess.CalledProcessError:
                # 没有变更需要提交
                logger.info("没有变更需要提交")

            # 使用 git subtree 只推送 frontend 目录到 main 分支
            logger.info("正在使用 git subtree 推送 frontend 目录...")

            # 创建临时分支用于 subtree
            subprocess.run(
                ["git", "subtree", "split", "--prefix=frontend", "-b", "frontend-temp"],
                cwd=project_root,
                check=True,
            )

            # 强制推送到远程 main 分支
            subprocess.run(
                ["git", "push", "-f", "origin", "frontend-temp:main"],
                cwd=project_root,
                check=True,
            )

            # 删除临时分支
            subprocess.run(
                ["git", "branch", "-D", "frontend-temp"],
                cwd=project_root,
                check=True,
            )

            logger.info("Git 同步成功: frontend 目录已推送到 main 分支")

            return {
                "success": True,
                "message": "frontend 目录已推送到 main 分支",
            }

        except subprocess.CalledProcessError as e:
            # 清理临时分支
            try:
                subprocess.run(
                    ["git", "branch", "-D", "frontend-temp"],
                    cwd=project_root,
                    capture_output=True,
                )
            except Exception:
                pass
            return {
                "success": False,
                "message": f"Git 操作失败: {e}",
            }
        except Exception as e:
            # 清理临时分支
            try:
                subprocess.run(
                    ["git", "branch", "-D", "frontend-temp"],
                    cwd=project_root,
                    capture_output=True,
                )
            except Exception:
                pass
            return {
                "success": False,
                "message": f"同步失败: {e}",
            }

    def generate_summary(self, title: str, content: str) -> str:
        """
        生成文章摘要

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            生成的摘要
        """
        return self.llm.generate_summary(title, content)

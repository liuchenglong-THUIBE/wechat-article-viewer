"""微信公众平台认证管理器"""

import time
from typing import Any

import requests
from playwright.sync_api import Page

from ..utils.logger import get_module_logger
from .browser_manager import BrowserManager
from .session_manager import SessionManager

logger = get_module_logger(__name__)

# 微信公众平台 URL
WECHAT_MP_URL = "https://mp.weixin.qq.com"


class WechatAuthenticator:
    """微信公众平台认证管理器"""

    def __init__(self):
        """初始化认证管理器"""
        self.session_manager = SessionManager()
        self.browser_manager = BrowserManager()
        self.login_url = f"{WECHAT_MP_URL}/"

    def ensure_authenticated(self, allow_browser_login: bool = True) -> bool:
        """
        确保已认证（自动处理会话复用和登录）

        Args:
            allow_browser_login: 会话不可用时是否允许打开浏览器扫码登录

        Returns:
            是否认证成功
        """
        logger.info("开始认证流程...")

        # 1. 检查会话文件是否存在且格式有效
        if self.session_manager.is_session_valid():
            logger.info("发现有效的会话文件，尝试验证...")

            # 2. 验证会话是否真实可用
            if self._verify_session():
                logger.info("会话验证成功，可以直接使用")
                return True

            logger.warning("会话验证失败")
        else:
            logger.info("未找到有效会话")

        if not allow_browser_login:
            logger.warning("当前模式禁止自动打开浏览器登录，请用户稍后手动登录后重试")
            return False

        # 3. 启动浏览器登录
        logger.info("允许浏览器登录，开始登录流程")
        return self._do_browser_login()

    def _verify_session(self) -> bool:
        """
        验证会话是否真实有效

        Returns:
            会话是否有效
        """
        try:
            session_data = self.session_manager.load_session()
            if not session_data or not session_data.get("cookies"):
                return False

            # 构造cookies字典
            cookies = {cookie["name"]: cookie["value"] for cookie in session_data["cookies"]}

            # 尝试访问微信公众平台首页
            response = requests.get(
                self.login_url,
                cookies=cookies,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=10,
                allow_redirects=True,
            )

            # 检查是否跳转到登录后的页面
            if any(keyword in response.url for keyword in ["cgi-bin/home", "token=", "home/index"]):
                logger.info(f"会话有效，当前URL: {response.url}")
                self._update_cookies_from_response(response, session_data)
                return True

            logger.warning(f"会话已失效，被重定向到: {response.url}")
            return False

        except Exception as e:
            logger.warning(f"验证会话时出错: {e}")
            return False


    def _update_cookies_from_response(self, response: requests.Response, old_session_data: dict) -> None:
        """
        从请求响应中提取并更新可能已刷新的 cookies
        """
        try:
            if not response.cookies:
                return

            # 获取所有当前缓存的 cookie
            old_cookies = old_session_data.get("cookies", [])
            cookie_dict = {c["name"]: c for c in old_cookies}
            
            updated = False
            for cookie in response.cookies:
                name = cookie.name
                value = cookie.value
                
                # 如果 cookie 存在且发生变化，或者是一个新的 cookie
                if name not in cookie_dict or cookie_dict[name].get("value") != value:
                    if name not in cookie_dict:
                        cookie_dict[name] = {"name": name, "value": value, "domain": cookie.domain or ".qq.com", "path": cookie.path or "/"}
                    else:
                        cookie_dict[name]["value"] = value
                    updated = True
                    
            if updated:
                new_cookies = list(cookie_dict.values())
                token = old_session_data.get("token")
                other_data = old_session_data.get("other_data")
                self.session_manager.save_session(new_cookies, token, other_data)
                logger.info("已在验证时更新并持久化最新的 cookies")
        except Exception as e:
            logger.debug(f"更新 cookies 失败: {e}")

    def _do_browser_login(self) -> bool:
        """
        执行浏览器登录流程

        Returns:
            是否登录成功
        """
        try:
            logger.info("启动浏览器进行登录...")

            # 启动浏览器（非无头模式，用户可见）
            page = self.browser_manager.start(headless=False)

            # 访问登录页面
            logger.info(f"正在访问: {self.login_url}")
            page.goto(self.login_url, wait_until="domcontentloaded", timeout=30000)

            # 等待页面稳定
            time.sleep(2)

            # 检查是否已经登录
            current_url = page.url
            if any(keyword in current_url for keyword in ["cgi-bin/home", "token=", "home/index"]):
                logger.info(f"检测到浏览器已登录，当前URL: {current_url}")
                self._save_session(page)
                return True

            # 需要扫码登录
            logger.info("请在浏览器中使用微信扫码登录...")
            logger.info("=" * 60)
            logger.info("等待用户扫码...")
            logger.info("=" * 60)

            # 等待登录成功
            if self._wait_for_login(page):
                self._save_session(page)
                return True

            return False

        except Exception as e:
            logger.error(f"浏览器登录失败: {e}", exc_info=True)
            return False
        finally:
            # 登录完成后关闭浏览器
            self.browser_manager.stop()

    def _wait_for_login(self, page: Page, timeout: int = 300) -> bool:
        """
        等待用户扫码登录

        Args:
            page: 浏览器页面对象
            timeout: 超时时间（秒）

        Returns:
            是否登录成功
        """
        start_time = time.time()
        initial_url = page.url
        logger.info(f"初始URL: {initial_url}")
        logger.info(f"开始监听登录，超时时间: {timeout}秒")

        check_count = 0
        last_log_time = start_time

        while time.time() - start_time < timeout:
            check_count += 1

            try:
                # 获取当前URL
                try:
                    current_url = page.evaluate("() => window.location.href")
                except Exception as e:
                    logger.debug(f"通过evaluate获取URL失败: {e}")
                    current_url = page.url

                # 每5秒打印一次当前URL
                current_time = time.time()
                if current_time - last_log_time >= 5:
                    elapsed = int(current_time - start_time)
                    logger.info(f"[{elapsed}s] 当前URL: {current_url}")
                    last_log_time = current_time

                # 检查URL是否包含登录成功的特征
                if any(
                    keyword in current_url for keyword in ["cgi-bin/home", "token=", "home/index"]
                ):
                    logger.info(f"检测到登录成功！URL: {current_url}")
                    time.sleep(2)
                    return True

            except Exception as e:
                logger.debug(f"检查登录状态时出错: {e}")

            # 等待1秒再检查
            time.sleep(1)

        logger.warning(f"登录超时（{timeout}秒），未检测到登录成功")
        return False

    def _save_session(self, page: Page):
        """
        保存登录会话数据

        Args:
            page: 浏览器页面对象
        """
        try:
            logger.info("开始保存会话数据...")

            # 获取cookies
            cookies = self.browser_manager.get_cookies()
            logger.info(f"获取到 {len(cookies)} 个cookies")

            # 提取token
            token = None
            for cookie in cookies:
                if cookie.get("name") == "token":
                    token = cookie.get("value")
                    logger.info(f"从cookies中找到token: {token[:20] if token else 'None'}...")
                    break

            if not token:
                # 尝试从URL中提取token
                url = page.url
                logger.info(f"当前URL: {url}")
                if "token=" in url:
                    token = url.split("token=")[1].split("&")[0]
                    logger.info(f"从URL中提取token: {token[:20] if token else 'None'}...")

            # 保存会话
            if self.session_manager.save_session(cookies, token):
                logger.info("会话保存成功")
            else:
                logger.warning("会话保存失败")

        except Exception as e:
            logger.error(f"保存会话失败: {e}", exc_info=True)

    def get_session_data(self) -> dict[str, Any] | None:
        """
        获取当前会话数据

        Returns:
            会话数据字典，失败返回None
        """
        return self.session_manager.load_session()

    def logout(self):
        """登出并清除会话"""
        self.session_manager.clear_session()
        self.browser_manager.stop()
        logger.info("已登出")

    def get_article_content_from_url(self, url: str) -> tuple[bool, str, str | None, str | None]:
        """
        从文章链接提取正文内容、发布时间和标题

        Args:
            url: 文章链接

        Returns:
            (是否成功, 正文内容, 发布时间字符串, 文章标题)
        """
        try:
            # 确保已认证
            if not self.ensure_authenticated():
                logger.error(f"认证失败，无法提取文章: {url}")
                return False, "", None, None

            # 使用已认证的session获取页面
            session_data = self.get_session_data()
            if not session_data:
                logger.error(f"获取会话数据失败: {url}")
                return False, "", None, None

            # 使用requests获取页面
            cookie_list = session_data.get("cookies", [])
            cookies = {}
            for cookie in cookie_list:
                if cookie.get("name") and cookie.get("value") is not None:
                    cookies[cookie["name"]] = cookie["value"]
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://mp.weixin.qq.com/",
            }

            response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
            response.raise_for_status()
            html = response.text

            # 提取正文内容和发布时间
            from bs4 import BeautifulSoup
            import re
            from datetime import datetime
            soup = BeautifulSoup(html, "html.parser")

            # 提取标题
            title = None
            title_tag = soup.find("h1", class_="rich_media_title")
            if title_tag:
                title = title_tag.get_text().strip()
            if not title:
                title_tag = soup.find("title")
                if title_tag:
                    title = title_tag.get_text().strip()
            if not title:
                title = "未知标题"

            publish_time_str = None
            time_tag = soup.find("em", id="publish_time")
            if time_tag:
                time_str = time_tag.get_text().strip()
                try:
                    publish_time_str = datetime.strptime(time_str, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00")
                except ValueError:
                    pass

            if not publish_time_str:
                scripts = soup.find_all("script")
                for script in scripts:
                    if script.string and "svr_time" in script.string:
                        match = re.search(r'"publish_time"\s*:\s*"(\d{4}-\d{2}-\d{2})"', script.string)
                        if match:
                            try:
                                publish_time_str = datetime.strptime(match.group(1), "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00")
                            except ValueError:
                                pass
                            break

            # 微信文章正文在 id="js_content" 的div中
            content_div = soup.find(id="js_content")
            if not content_div:
                logger.warning(f"未找到文章内容区域: {url}")
                return False, "", publish_time_str, title

            # 获取所有p标签文本
            paragraphs = []
            for p in content_div.find_all(["p", "section"]):
                text = p.get_text().strip()
                if text and "Copyright" not in text and "微信公众号" not in text and "二维码" not in text and "赞" not in text and "在看" not in text:
                    paragraphs.append(text)

            content = "\n\n".join(paragraphs)
            logger.info(f"成功提取文章正文: {url}, 长度: {len(content)}")
            return True, content, publish_time_str, title

        except Exception as e:
            logger.error(f"提取文章正文失败 {url}: {e}")
            return False, "", None, None

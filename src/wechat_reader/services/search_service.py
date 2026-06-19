"""公众号搜索服务"""

from typing import Any

import requests

from ..utils.logger import get_module_logger

logger = get_module_logger(__name__)

WECHAT_MP_URL = "https://mp.weixin.qq.com"


class SearchService:
    """公众号搜索服务"""

    def __init__(self):
        """初始化搜索服务"""
        pass

    def search_public_accounts(
        self, keyword: str, session_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        搜索公众号

        Args:
            keyword: 搜索关键词
            session_data: 认证会话数据

        Returns:
            搜索结果列表
        """
        try:
            url = f"{WECHAT_MP_URL}/cgi-bin/searchbiz"
            params = {
                "action": "search_biz",
                "begin": 0,
                "count": 10,
                "query": keyword,
                "token": session_data.get("token", ""),
                "lang": "zh_CN",
                "f": "json",
                "ajax": 1,
            }

            cookies = {
                cookie["name"]: cookie["value"] for cookie in session_data.get("cookies", [])
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": WECHAT_MP_URL,
            }

            logger.info(f"开始搜索公众号: {keyword}")
            response = requests.get(
                url, params=params, cookies=cookies, headers=headers, timeout=30
            )
            result = response.json()

            if result.get("base_resp", {}).get("ret") != 0:
                error_msg = result.get("base_resp", {}).get("err_msg", "未知错误")
                logger.error(f"搜索失败: {error_msg}")
                return []

            results = []
            list_data = result.get("list", [])

            for item in list_data:
                account_info = {
                    "fakeid": item.get("fakeid", ""),
                    "nickname": item.get("nickname", ""),
                    "alias": item.get("alias", ""),
                    "round_head_img": item.get("round_head_img", ""),
                    "service_type": item.get("service_type", ""),
                    "signature": item.get("signature", ""),
                }
                results.append(account_info)

            logger.info(f"搜索完成，找到 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"搜索公众号异常: {e}", exc_info=True)
            return []

    def get_account_articles(
        self, fakeid: str, session_data: dict[str, Any], count: int = 20
    ) -> list[dict[str, Any]]:
        """
        获取公众号文章列表

        Args:
            fakeid: 公众号的 fakeid
            session_data: 认证会话数据
            count: 获取文章数量

        Returns:
            文章列表
        """
        try:
            url = f"{WECHAT_MP_URL}/cgi-bin/appmsg"

            # 尝试不同的参数组合
            params_list = [
                {
                    "action": "list_ex",
                    "fakeid": fakeid,
                    "begin": 0,
                    "count": count,
                    "query": "",
                    "token": session_data.get("token", ""),
                    "lang": "zh_CN",
                    "f": "json",
                    "ajax": 1,
                },
                {
                    "action": "list",
                    "fakeid": fakeid,
                    "begin": 0,
                    "count": count,
                    "token": session_data.get("token", ""),
                    "lang": "zh_CN",
                    "f": "json",
                    "ajax": 1,
                }
            ]

            cookies = {
                cookie["name"]: cookie["value"] for cookie in session_data.get("cookies", [])
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Referer": WECHAT_MP_URL,
                "X-Requested-With": "XMLHttpRequest",
            }

            logger.info(f"获取公众号文章，fakeid: {fakeid}")
            logger.info(f"Token: {session_data.get('token', 'None')}")
            logger.info(f"Cookies count: {len(cookies)}")

            # 尝试不同的参数组合
            for params in params_list:
                try:
                    logger.info(f"尝试参数: {params}")
                    response = requests.get(
                        url, params=params, cookies=cookies, headers=headers, timeout=30
                    )
                    logger.info(f"Response status: {response.status_code}")
                    logger.info(f"Response URL: {response.url}")
                    result = response.json()

                    if result.get("base_resp", {}).get("ret") == 0:
                        articles = []
                        app_msg_list = result.get("app_msg_list", [])

                        for item in app_msg_list:
                            article_info = {
                                "title": item.get("title", ""),
                                "link": item.get("link", ""),
                                "cover": item.get("cover", ""),
                                "digest": item.get("digest", ""),
                                "create_time": item.get("update_time") or item.get("create_time", 0),
                                "author": item.get("author", ""),
                            }
                            articles.append(article_info)

                        logger.info(f"获取完成，找到 {len(articles)} 篇文章")
                        return articles
                    else:
                        error_msg = result.get("base_resp", {}).get("err_msg", "未知错误")
                        logger.warning(f"参数组合失败: {error_msg}")
                except Exception as e:
                    logger.warning(f"参数组合异常: {e}")

            logger.error("所有参数组合都失败")
            return []

        except Exception as e:
            logger.error(f"获取公众号文章异常: {e}", exc_info=True)
            return []

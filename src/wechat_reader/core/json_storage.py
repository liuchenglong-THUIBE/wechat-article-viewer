"""
JSON 数据存储模块

替代 SQLite，直接读写 JSON 文件
数据存储在 frontend/api/ 目录下，直接用于前端展示
"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..utils.logger import get_module_logger

logger = get_module_logger(__name__)


class JsonStorage:
    """
    JSON 数据存储管理器

    数据直接存储在 frontend/api/ 目录：
    - articles.json: 文章数据
    - accounts.json: 公众号数据
    - monitors.json: 监控列表
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化存储

        Args:
            data_dir: 数据目录，默认为 frontend/api/
        """
        if data_dir is None:
            # 默认在项目根目录的 frontend/api/
            project_root = Path(__file__).parent.parent.parent.parent
            self.data_dir = project_root / "frontend" / "api"
        else:
            self.data_dir = Path(data_dir)

        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 读写锁，防止多线程写入冲突
        self._lock = threading.Lock()

        # 初始化空数据文件
        self._init_if_not_exists()

    def _init_if_not_exists(self):
        """如果数据文件不存在，创建空文件"""
        files = {
            "articles.json": [],
            "accounts.json": [],
            "monitors.json": []
        }

        for filename, default_data in files.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                self._write_json(filepath, default_data)
                logger.info(f"创建数据文件: {filepath}")

    def _read_json(self, filename: str) -> list[dict]:
        """读取 JSON 文件"""
        filepath = self.data_dir / filename
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"读取 {filename} 失败: {e}")
            return []

    def _write_json(self, filepath: Path, data: list[dict]):
        """写入 JSON 文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"写入 {filepath} 失败: {e}")
            raise

    # ==================== 文章操作 ====================

    def get_all_articles(self) -> list[dict]:
        """获取所有文章"""
        return self._read_json("articles.json")

    def get_article_by_id(self, article_id: int) -> Optional[dict]:
        """根据 ID 获取文章"""
        articles = self.get_all_articles()
        for article in articles:
            if article.get("id") == article_id:
                return article
        return None

    def get_article_by_link(self, link: str) -> Optional[dict]:
        """根据链接获取文章（用于去重）"""
        articles = self.get_all_articles()
        for article in articles:
            if article.get("article_link") == link or article.get("link") == link:
                return article
        return None

    def add_article(self, article_data: dict) -> dict:
        """
        添加文章

        Args:
            article_data: 文章数据

        Returns:
            添加后的文章（包含生成的 id）
        """
        with self._lock:
            articles = self.get_all_articles()

            # 生成新 ID
            max_id = max([a.get("id", 0) for a in articles], default=0)
            article_data["id"] = max_id + 1

            # 添加时间戳
            if "created_at" not in article_data:
                article_data["created_at"] = datetime.now().isoformat()

            articles.append(article_data)

            # 写入文件
            self._write_json(self.data_dir / "articles.json", articles)
            logger.info(f"添加文章: {article_data.get('article_title', '无标题')}")

            return article_data
    def update_article(self, article_id: int, updates: dict) -> Optional[dict]:
        """更新文章"""
        with self._lock:
            articles = self.get_all_articles()

            for i, article in enumerate(articles):
                if article.get("id") == article_id:
                    articles[i].update(updates)
                    articles[i]["updated_at"] = datetime.now().isoformat()
                    self._write_json(self.data_dir / "articles.json", articles)
                    return articles[i]

            return None
    def delete_article(self, article_id: int) -> bool:
        """删除文章"""
        with self._lock:
            articles = self.get_all_articles()
            original_len = len(articles)
            articles = [a for a in articles if a.get("id") != article_id]

            if len(articles) < original_len:
                self._write_json(self.data_dir / "articles.json", articles)
                return True
            return False
    def get_articles_by_account(self, account_name: str) -> list[dict]:
        """获取指定公众号的文章"""
        articles = self.get_all_articles()
        return [
            a for a in articles
            if a.get("account_name") == account_name or a.get("accountName") == account_name
        ]

    def article_exists(self, link: str) -> bool:
        """检查文章是否已存在（根据链接）"""
        return self.get_article_by_link(link) is not None

    # ==================== 公众号操作 ====================

    def get_all_accounts(self) -> list[dict]:
        """获取所有公众号"""
        return self._read_json("accounts.json")

    def get_account_by_name(self, account_name: str) -> Optional[dict]:
        """根据名称获取公众号"""
        accounts = self.get_all_accounts()
        for account in accounts:
            if account.get("account_name") == account_name or account.get("name") == account_name:
                return account
        return None

    def add_account(self, account_data: dict) -> dict:
        """添加公众号"""
        with self._lock:
            accounts = self.get_all_accounts()

            # 检查是否已存在
            existing = self.get_account_by_name(account_data.get("account_name", ""))
            if existing:
                return existing

            # 生成新 ID
            max_id = max([a.get("id", 0) for a in accounts], default=0)
            account_data["id"] = max_id + 1

            if "fakeid" not in account_data and "account_id" in account_data:
                account_data["fakeid"] = account_data.pop("account_id")

            accounts.append(account_data)
            self._write_json(self.data_dir / "accounts.json", accounts)

            logger.info(f"添加公众号: {account_data.get('account_name', '未知')}")
            return account_data
    def update_account(self, account_id: int, updates: dict) -> Optional[dict]:
        """更新公众号"""
        with self._lock:
            accounts = self.get_all_accounts()

            for i, account in enumerate(accounts):
                if account.get("id") == account_id:
                    accounts[i].update(updates)
                    # 确保如果更新传入了 account_id 则重命名为 fakeid
                    if "account_id" in accounts[i]:
                        accounts[i]["fakeid"] = accounts[i].pop("account_id")
                    self._write_json(self.data_dir / "accounts.json", accounts)
                    return accounts[i]

            return None
    def delete_account(self, account_id: int) -> bool:
        """删除公众号"""
        with self._lock:
            accounts = self.get_all_accounts()
            original_len = len(accounts)
            accounts = [a for a in accounts if a.get("id") != account_id]

            if len(accounts) < original_len:
                self._write_json(self.data_dir / "accounts.json", accounts)
                return True
            return False

        # ==================== 监控列表操作 ====================
    def get_all_monitors(self) -> list[dict]:
        """获取所有监控的公众号"""
        return self._read_json("monitors.json")

    def add_monitor(self, account_name: str, fakeid: str = "") -> dict:
        """添加监控"""
        with self._lock:
            monitors = self.get_all_monitors()

            # 检查是否已存在
            for m in monitors:
                if m.get("account_name") == account_name:
                    # 如果之前没有fakeid，现在有了，就更新
                    if fakeid and not m.get("fakeid"):
                        m["fakeid"] = fakeid
                        self._write_json(self.data_dir / "monitors.json", monitors)
                    return m

            monitor = {
                "account_name": account_name,
                "fakeid": fakeid
            }

            monitors.append(monitor)
            self._write_json(self.data_dir / "monitors.json", monitors)

            logger.info(f"添加监控: {account_name}")
            return monitor
    def remove_monitor(self, account_name: str) -> bool:
        """移除监控"""
        with self._lock:
            monitors = self.get_all_monitors()
            original_len = len(monitors)
            monitors = [m for m in monitors if m.get("account_name") != account_name]

            if len(monitors) < original_len:
                self._write_json(self.data_dir / "monitors.json", monitors)
                return True
            return False
    def is_monitoring(self, account_name: str) -> bool:
        """检查是否在监控列表中"""
        monitors = self.get_all_monitors()
        return any(m.get("account_name") == account_name for m in monitors)


# 全局存储实例
_storage_instance: Optional[JsonStorage] = None


def get_storage(data_dir: Optional[Path] = None) -> JsonStorage:
    """
    获取存储实例（单例模式）

    Args:
        data_dir: 数据目录

    Returns:
        JsonStorage 实例
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = JsonStorage(data_dir)
    return _storage_instance


def reset_storage():
    """重置存储实例（用于测试）"""
    global _storage_instance
    _storage_instance = None

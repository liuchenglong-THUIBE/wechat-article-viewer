"""文章管理服务"""

from typing import Any, Optional

from ..utils.logger import get_module_logger

logger = get_module_logger(__name__)


class ArticleService:
    """文章管理服务"""

    def __init__(self, storage=None):
        """初始化文章服务"""
        self.storage = storage

    def get_all_articles(self) -> list[dict[str, Any]]:
        """
        获取所有文章

        Returns:
            文章列表
        """
        if self.storage:
            return self.storage.get_all_articles()
        return []

    def get_article_by_id(self, article_id: int) -> dict[str, Any] | None:
        """
        根据ID获取文章

        Args:
            article_id: 文章ID

        Returns:
            文章信息，不存在返回None
        """
        if self.storage:
            return self.storage.get_article_by_id(article_id)
        return None

    def create_article(self, article_data: dict[str, Any]) -> tuple[bool, str, int | None]:
        """
        创建文章

        Args:
            article_data: 文章数据

        Returns:
            (是否成功, 消息, 文章ID)
        """
        try:
            if self.storage:
                article = self.storage.add_article(article_data)
                logger.info(f"创建文章成功: {article.get('article_title', '无标题')}")
                return True, "创建成功", article.get("id")
            return False, "存储未初始化", None

        except Exception as e:
            logger.error(f"创建文章失败: {e}")
            return False, f"创建失败: {str(e)}", None

    def delete_article(self, article_id: int) -> tuple[bool, str]:
        """
        删除文章

        Args:
            article_id: 文章ID

        Returns:
            (是否成功, 消息)
        """
        try:
            if self.storage:
                if self.storage.delete_article(article_id):
                    logger.info(f"删除文章成功: {article_id}")
                    return True, "删除成功"
                else:
                    return False, "文章不存在"
            return False, "存储未初始化"

        except Exception as e:
            logger.error(f"删除文章失败: {e}")
            return False, f"删除失败: {str(e)}"

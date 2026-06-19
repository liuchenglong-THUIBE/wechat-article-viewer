"""公众号管理服务"""

from typing import Any, Optional

from ..utils.logger import get_module_logger

logger = get_module_logger(__name__)


class WechatService:
    """公众号管理服务"""

    def __init__(self, storage=None):
        """初始化公众号服务"""
        self.storage = storage

    def get_all_accounts(self) -> list[dict[str, Any]]:
        """
        获取所有公众号列表

        Returns:
            公众号列表
        """
        if self.storage:
            return self.storage.get_all_accounts()
        return []

    def get_account_by_id(self, account_id: int) -> dict[str, Any] | None:
        """
        根据ID获取公众号

        Args:
            account_id: 公众号ID

        Returns:
            公众号信息，不存在返回None
        """
        accounts = self.get_all_accounts()
        for account in accounts:
            if account.get("id") == account_id:
                return account
        return None

    def create_account(self, account_data: dict[str, Any]) -> tuple[bool, str, int | None]:
        """
        创建公众号

        Args:
            account_data: 公众号数据

        Returns:
            (是否成功, 消息, 公众号ID)
        """
        try:
            account_name = account_data.get("account_name", "").strip()
            if not account_name:
                return False, "公众号名称不能为空", None

            if self.storage:
                # 检查是否已存在
                existing = self.storage.get_account_by_name(account_name)
                if existing:
                    return True, "该公众号已存在", existing.get("id")

                # 创建公众号
                account = self.storage.add_account({
                    "account_name": account_name,
                    "account_id": account_data.get("fakeid", ""),
                    "description": account_data.get("description", ""),
                })

                logger.info(f"创建公众号成功: {account_name}")
                return True, "创建成功", account.get("id")
            else:
                return False, "存储未初始化", None

        except Exception as e:
            logger.error(f"创建公众号失败: {e}")
            return False, f"创建失败: {str(e)}", None

    def delete_account(self, account_id: int) -> tuple[bool, str]:
        """
        删除公众号

        Args:
            account_id: 公众号ID

        Returns:
            (是否成功, 消息)
        """
        try:
            if self.storage:
                if self.storage.delete_account(account_id):
                    logger.info(f"删除公众号成功: ID {account_id}")
                    return True, "删除成功"
                else:
                    return False, "公众号不存在"
            return False, "存储未初始化"

        except Exception as e:
            logger.error(f"删除公众号失败: {e}")
            return False, f"删除失败: {str(e)}"

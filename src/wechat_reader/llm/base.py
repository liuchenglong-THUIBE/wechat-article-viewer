"""
LLM 提供者基类
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """LLM 提供者抽象基类"""

    @abstractmethod
    def generate_summary(self, title: str, content: str) -> str:
        """
        生成文章摘要

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            生成的摘要
        """
        pass

    @abstractmethod
    def analyze_account_theme(self, account_name: str, description: str) -> str:
        """
        分析公众号的详细内容画像

        Args:
            account_name: 公众号名称
            description: 公众号简介

        Returns:
            约 100 字的详细内容描述
        """
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查 LLM 是否可用

        Returns:
            是否可用
        """
        pass

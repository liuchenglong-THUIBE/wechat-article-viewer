"""
微信公众号阅读器

一个用于采集微信公众号文章、生成 AI 摘要并部署到静态网站的工具。
"""

__version__ = "1.0.0"
__author__ = "Author"
__email__ = "author@example.com"

from .core.reader import WechatReader
from .core.config import Config

__all__ = ["WechatReader", "Config"]

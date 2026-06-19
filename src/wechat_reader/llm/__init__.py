"""
LLM 模块

使用方式：
    from wechat_reader.llm import create_llm_provider

    llm = create_llm_provider()
    summary = llm.generate_summary(title, content)

配置方式（推荐）：
    在 config.json 中配置 LLM 参数：
    {
        "llm_api_key": "your-api-key",
        "llm_model": "minimax/minimax-m2.5:free",
        "llm_base_url": "https://openrouter.ai/api/v1"
    }

支持的 LLM 平台：
- OpenRouter (推荐，支持多种免费模型)
- OpenAI
- 豆包
- 其他兼容 OpenAI API 格式的平台

详细配置示例请参考 llm_config.py 文件底部的注释
"""

from .base import LLMProvider
from .llm_config import LLMConfig
from .openai_provider import OpenAIProvider

__all__ = [
    "LLMProvider",
    "OpenAIProvider",
    "LLMConfig",
    "create_llm_provider",
]


def create_llm_provider(config: LLMConfig = None) -> LLMProvider:
    """
    根据配置创建 LLM 提供者实例

    配置优先级（从高到低）：
    1. config.json 配置文件
    2. 环境变量
    3. llm_config.py 中的默认值

    Args:
        config: LLMConfig 实例，默认使用 LLMConfig 类配置

    Returns:
        LLMProvider 实例

    Examples:
        >>> # 使用 config.json 配置（推荐）
        >>> llm = create_llm_provider()
        >>>
        >>> # 使用自定义配置
        >>> from wechat_reader.llm.llm_config import LLMConfig
        >>> LLMConfig.API_KEY = "your-key"
        >>> LLMConfig.MODEL = "gpt-3.5-turbo"
        >>> llm = create_llm_provider()
    """
    # 获取实际生效的配置（优先从 config.json 读取）
    effective_config = LLMConfig.get_effective_config()

    # 检查是否配置了 API Key
    api_key = effective_config.get("api_key", "")
    if not api_key or api_key in ["", "your-api-key", "sk-your-openai-key", "sk-or-v1-xxx"]:
        raise RuntimeError(
            "未配置 LLM API Key。请在 config.json 中设置 'llm_api_key'，"
            "或修改 src/wechat_reader/llm/llm_config.py 中的 API_KEY。"
            "详细配置示例请参考 llm_config.py 文件。"
        )

    # 创建 OpenAI 格式提供者
    return OpenAIProvider(
        api_key=api_key,
        model=effective_config.get("model", LLMConfig.MODEL),
        base_url=effective_config.get("base_url", LLMConfig.BASE_URL),
        max_retries=effective_config.get("max_retries", LLMConfig.MAX_RETRIES),
        timeout=effective_config.get("timeout", LLMConfig.TIMEOUT),
    )


def get_current_config() -> dict:
    """
    获取当前配置信息（用于调试）

    Returns:
        包含配置信息的字典（隐藏 API Key）
    """
    effective_config = LLMConfig.get_effective_config()

    # 隐藏 API Key 的部分内容
    api_key = effective_config.get("api_key", "")
    if api_key and len(api_key) > 10:
        masked_key = api_key[:8] + "..." + api_key[-4:]
    else:
        masked_key = "未配置"

    return {
        "model": effective_config.get("model"),
        "base_url": effective_config.get("base_url"),
        "api_key": masked_key,
        "is_configured": bool(api_key and api_key not in ["", "your-api-key"]),
    }

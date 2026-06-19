"""
LLM 配置文件

配置优先级（从高到低）：
1. config.json 配置文件
2. 环境变量
3. 本文件的默认值

使用说明：
1. 推荐方式：在 config.json 中配置（会被自动读取）
2. 备用方式：修改本文件中的默认值
3. 临时方式：设置环境变量

支持的 LLM 平台：
- OpenRouter (推荐，支持多种免费/付费模型)
- OpenAI
- Azure OpenAI
- 其他兼容 OpenAI API 格式的平台
"""

from typing import Optional


class LLMConfig:
    """
    LLM 配置类

    注意：实际运行时，配置会从 config.json 自动读取并覆盖这些默认值。
    只有当 config.json 中未配置时，才会使用本文件的默认值。
    """

    # ============================================
    # 默认配置（会被 config.json 覆盖）
    # ============================================

    # API Key - 请从 config.json 或环境变量配置，不要硬编码
    API_KEY = ""

    # 模型名称
    # OpenRouter DeepSeek: "deepseek/deepseek-v4-flash"
    MODEL = "deepseek/deepseek-v4-flash"

    # API 基础 URL
    # OpenRouter: "https://openrouter.ai/api/v1"
    # OpenAI: "https://api.openai.com/v1"
    # 豆包: "https://ark.cn-beijing.volces.com/api/v3"
    BASE_URL = "https://openrouter.ai/api/v1"

    # ============================================
    # 高级配置（一般不需要修改）
    # ============================================

    # 重试配置
    MAX_RETRIES = 3  # 最大重试次数
    TIMEOUT = 60.0  # 请求超时时间（秒）

    # 请求配置
    MAX_TOKENS = 500  # 最大生成 token 数
    TEMPERATURE = 0.7  # 温度参数（创造性程度）

    # 摘要配置
    CONTENT_MAX_LENGTH = 3000  # 文章内容截断长度

    @classmethod
    def to_dict(cls) -> dict:
        """转换为字典格式"""
        return {
            "api_key": cls.API_KEY,
            "model": cls.MODEL,
            "base_url": cls.BASE_URL,
            "max_retries": cls.MAX_RETRIES,
            "timeout": cls.TIMEOUT,
            "max_tokens": cls.MAX_TOKENS,
            "temperature": cls.TEMPERATURE,
        }

    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置 API Key"""
        # 优先检查运行时配置（从 config.json 加载的）
        runtime_config = cls._get_runtime_config()
        if runtime_config and runtime_config.get("api_key"):
            return True

        # 检查本文件的默认值
        return bool(
            cls.API_KEY
            and cls.API_KEY not in [
                "",
                "your-api-key",
                "sk-your-openai-key",
                "sk-or-v1-xxx",
            ]
        )

    @classmethod
    def _get_runtime_config(cls) -> Optional[dict]:
        """
        获取运行时配置（从 config.json 加载）

        Returns:
            配置字典，如果无法获取则返回 None
        """
        try:
            # 延迟导入，避免循环依赖
            from ..core.config import Config
            config = Config()
            llm_config = config.get_llm_config()
            if llm_config.get("api_key"):
                return {
                    "api_key": llm_config.get("api_key"),
                    "model": llm_config.get("model", cls.MODEL),
                    "base_url": llm_config.get("base_url", cls.BASE_URL),
                }
        except Exception:
            pass
        return None

    @classmethod
    def get_effective_config(cls) -> dict:
        """
        获取实际生效的配置（合并运行时配置和默认值）

        Returns:
            实际生效的配置字典
        """
        runtime = cls._get_runtime_config()

        if runtime:
            return {
                "api_key": runtime.get("api_key", cls.API_KEY),
                "model": runtime.get("model", cls.MODEL),
                "base_url": runtime.get("base_url", cls.BASE_URL),
                "max_retries": cls.MAX_RETRIES,
                "timeout": cls.TIMEOUT,
            }

        return {
            "api_key": cls.API_KEY,
            "model": cls.MODEL,
            "base_url": cls.BASE_URL,
            "max_retries": cls.MAX_RETRIES,
            "timeout": cls.TIMEOUT,
        }


# ============================================
# 常用配置示例（复制到 config.json 中使用）
# ============================================
#
# -------- OpenRouter + MiniMax (免费) --------
# {
#   "llm_api_key": "sk-or-v1-xxx",
#   "llm_model": "minimax/minimax-m2.5:free",
#   "llm_base_url": "https://openrouter.ai/api/v1"
# }
#
# -------- OpenRouter + Google Gemini (免费) --------
# {
#   "llm_api_key": "sk-or-v1-xxx",
#   "llm_model": "google/gemini-2.0-flash-exp:free",
#   "llm_base_url": "https://openrouter.ai/api/v1"
# }
#
# -------- OpenRouter + DeepSeek (免费) --------
# {
#   "llm_api_key": "sk-or-v1-xxx",
#   "llm_model": "deepseek/deepseek-chat:free",
#   "llm_base_url": "https://openrouter.ai/api/v1"
# }
#
# -------- OpenRouter + 豆包 --------
# {
#   "llm_api_key": "sk-or-v1-xxx",
#   "llm_model": "doubao/doubao-seed-2-0-lite-260215",
#   "llm_base_url": "https://openrouter.ai/api/v1"
# }
#
# -------- 豆包直接接入 --------
# {
#   "llm_api_key": "your-doubao-api-key",
#   "llm_model": "doubao-seed-2-0-lite-260215",
#   "llm_base_url": "https://ark.cn-beijing.volces.com/api/v3"
# }
#
# -------- OpenAI --------
# {
#   "llm_api_key": "sk-xxx",
#   "llm_model": "gpt-3.5-turbo",
#   "llm_base_url": "https://api.openai.com/v1"
# }
#
# ============================================

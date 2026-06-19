"""
OpenAI 格式 LLM 提供者

支持所有兼容 OpenAI API 格式的平台，包括：
- OpenRouter
- OpenAI
- Azure OpenAI
- 其他兼容平台
"""

from typing import Optional

from openai import OpenAI

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """
    OpenAI 格式 API 提供者

    使用 openai 库调用兼容 OpenAI API 格式的服务
    """

    def __init__(
        self,
        api_key: str,
        model: str = "minimax/minimax-m2.5:free",
        base_url: str = "https://openrouter.ai/api/v1",
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        """
        初始化 OpenAI 提供者

        Args:
            api_key: API 密钥
            model: 模型名称
            base_url: API 基础 URL
            max_retries: 最大重试次数
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries

        # 创建 OpenAI 客户端
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            max_retries=max_retries,
            timeout=timeout,
        )

    @property
    def is_available(self) -> bool:
        """检查是否可用（有 API Key）"""
        return bool(self.api_key)

    def generate_summary(self, title: str, content: str) -> str:
        """
        生成文章摘要

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            生成的摘要
        """
        if not self.is_available:
            raise RuntimeError("未配置 API Key")

        # 截断内容，避免过长
        content = content[:3000] if len(content) > 3000 else content

        prompt = self._build_prompt(title, content)

        # 构建请求参数
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500,
        }

        # 显式关闭推理/思考能力，以提高响应速度和降低 token 消耗
        if "deepseek" in self.model.lower() or "minimax" in self.model.lower():
            kwargs["extra_body"] = {"reasoning": {"enabled": False}}

        response = self.client.chat.completions.create(**kwargs)

        return response.choices[0].message.content.strip()

    def analyze_account_theme(self, account_name: str, description: str) -> str:
        """
        分析公众号详细内容画像

        Args:
            account_name: 公众号名称
            description: 公众号简介

        Returns:
            约 100 字的内容描述
        """
        if not self.is_available:
            return "未知内容画像"

        prompt = f"""作为资深的新媒体观察员，请你根据以下微信公众号的“名称”和“官方简介”，深入分析并详细推断这个公众号主要是讲什么内容的。

名称: {account_name}
官方简介: {description or "无"}

要求：
1. 请输出一段大约 100 字的详细描述。
2. 描述需要精确、细致，说明该账号面向的目标人群、可能发布的文章类型以及核心内容方向。
3. 请使用客观、专业的分析口吻（例如：“该公众号主要聚焦于...”）。
4. 不要输出任何无关的问候语或解释。
"""
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "max_tokens": 300,
        }

        # 显式关闭推理/思考能力，以提高响应速度和降低 token 消耗
        if "deepseek" in self.model.lower() or "minimax" in self.model.lower():
            kwargs["extra_body"] = {"reasoning": {"enabled": False}}

        try:
            response = self.client.chat.completions.create(**kwargs)
            theme = response.choices[0].message.content.strip()
            return theme
        except Exception as e:
            return f"分析失败: {str(e)}"

    def generate_summary_with_reasoning(self, title: str, content: str) -> dict:
        """
        生成摘要（带推理过程）

        适用于支持 reasoning 的模型，如 minimax-m2.5

        Args:
            title: 文章标题
            content: 文章内容

        Returns:
            包含摘要和推理过程的字典
        """
        if not self.is_available:
            raise RuntimeError("未配置 API Key")

        content = content[:3000] if len(content) > 3000 else content
        prompt = self._build_prompt(title, content)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
            extra_body={"reasoning": {"enabled": True}},
        )

        message = response.choices[0].message

        result = {
            "summary": message.content.strip(),
            "reasoning": None,
        }

        # 获取推理过程（如果模型支持）
        if hasattr(message, "reasoning_details"):
            result["reasoning"] = message.reasoning_details

        return result

    def _build_prompt(self, title: str, content: str) -> str:
        """构建提示词"""
        return f"""请为以下文章写一个150-300字的摘要：

标题: {title}

正文:
{content}

要求：
1. 概括文章核心观点
2. 语言简洁流畅
3. 控制在150-300字之间
4. 输出格式要求：
   - 不要添加"摘要："等标题
   - 不要使用markdown格式（如**、#等）
   - 不要分段，输出为一段连续的文本
   - 直接输出摘要内容即可"""

    def generate_summary_stream(self, title: str, content: str):
        """
        流式生成摘要

        Args:
            title: 文章标题
            content: 文章内容

        Yields:
            生成的文本片段
        """
        if not self.is_available:
            raise RuntimeError("未配置 API Key")

        content = content[:3000] if len(content) > 3000 else content
        prompt = self._build_prompt(title, content)

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

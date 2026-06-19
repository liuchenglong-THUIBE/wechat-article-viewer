"""
配置管理模块

支持多种配置方式（优先级从高到低）：
1. 命令行参数
2. 环境变量
3. 配置文件
4. 默认值
"""

import json
import os
from pathlib import Path
from typing import Any, Optional


class Config:
    """配置管理类"""

    # 默认配置
    DEFAULTS = {
        "llm_provider": "openrouter",  # 可选: openrouter, direct, mock
        "llm_api_key": "",
        "llm_model": "minimax/minimax-m2.5:free",  # OpenRouter 默认模型
        "llm_base_url": "https://openrouter.ai/api/v1",
        "llm_site_url": "",  # OpenRouter 排名用
        "llm_site_name": "",  # OpenRouter 排名用
        "frontend_dir": "frontend",  # 前端目录
        "auto_git_push": True,
        "export_max_articles": 1000,
        "export_summary_only": False,
        "log_level": "INFO",
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，默认使用项目根目录下的 config.json
        """
        self._config = {}

        # 确定配置文件路径
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 默认在项目根目录
            project_root = Path(__file__).parent.parent.parent.parent
            self.config_path = project_root / "config.json"

        # 加载配置
        self._load()

    def _load(self) -> None:
        """加载配置"""
        # 1. 从默认值开始
        self._config = self.DEFAULTS.copy()

        # 2. 从配置文件加载
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    self._config.update(file_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告: 加载配置文件失败: {e}")

        # 3. 从环境变量加载（优先级更高）
        self._load_from_env()

    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        env_mappings = {
            "WECHAT_READER_LLM_PROVIDER": "llm_provider",
            "WECHAT_READER_LLM_API_KEY": "llm_api_key",
            "WECHAT_READER_LLM_MODEL": "llm_model",
            "WECHAT_READER_LLM_BASE_URL": "llm_base_url",
            "WECHAT_READER_LLM_SITE_URL": "llm_site_url",
            "WECHAT_READER_LLM_SITE_NAME": "llm_site_name",
            "WECHAT_READER_FRONTEND_DIR": "frontend_dir",
            "WECHAT_READER_AUTO_GIT_PUSH": "auto_git_push",
            "WECHAT_READER_LOG_LEVEL": "log_level",
        }

        for env_var, config_key in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # 类型转换
                if config_key in ["auto_git_push", "export_summary_only"]:
                    value = value.lower() in ("true", "1", "yes")
                elif config_key in ["export_max_articles"]:
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                self._config[config_key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键名
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        设置配置项

        Args:
            key: 配置键名
            value: 配置值
        """
        self._config[key] = value

    def save(self) -> None:
        """保存配置到文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"错误: 保存配置文件失败: {e}")

    def get_frontend_dir(self) -> Path:
        """获取前端目录路径"""
        path = self.get("frontend_dir", self.DEFAULTS["frontend_dir"])
        path_obj = Path(path)
        if not path_obj.is_absolute():
            project_root = Path(__file__).parent.parent.parent.parent
            path_obj = project_root / path_obj
        return path_obj

    def get_frontend_api_dir(self) -> Path:
        """获取前端 API 数据目录路径"""
        return self.get_frontend_dir() / "api"

    def get_llm_config(self) -> dict:
        """获取 LLM 配置"""
        return {
            "provider": self.get("llm_provider", "openrouter"),
            "api_key": self.get("llm_api_key", ""),
            "model": self.get("llm_model", self.DEFAULTS["llm_model"]),
            "base_url": self.get("llm_base_url", self.DEFAULTS["llm_base_url"]),
            "site_url": self.get("llm_site_url", ""),
            "site_name": self.get("llm_site_name", ""),
        }

    def to_dict(self) -> dict:
        """导出为字典"""
        return self._config.copy()

    def __repr__(self) -> str:
        return f"Config({self.config_path})"

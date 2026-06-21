"""会话管理模块 - 保存和加载微信公众平台登录会话"""

import json
import os
import time
from pathlib import Path
from typing import Any, cast


class SessionManager:
    """会话管理器"""

    def __init__(self, session_file: Path | None = None):
        """
        初始化会话管理器

        Args:
            session_file: 会话文件路径
        """
        if session_file is None:
            env_session_file = os.environ.get("WECHAT_READER_SESSION_FILE")
            if env_session_file:
                session_file = Path(env_session_file).expanduser()
            else:
                # 默认在项目根目录的 data 文件夹
                project_root = Path(__file__).parent.parent.parent.parent
                session_file = project_root / "data" / "session.json"

        self.session_file = session_file
        self.session_file.parent.mkdir(parents=True, exist_ok=True)

        # 缓存会话数据，避免频繁读取文件
        self._cached_session: dict[str, Any] | None = None
        self._cache_time: float = 0
        self._cache_ttl: int = 300  # 缓存5分钟

    def save_session(
        self,
        cookies: list[dict[str, Any]],
        token: str | None = None,
        other_data: dict[str, Any] | None = None,
    ) -> bool:
        """
        保存会话数据

        Args:
            cookies: Cookie列表
            token: Token值
            other_data: 其他数据

        Returns:
            是否保存成功
        """
        try:
            session_data = {"cookies": cookies, "token": token, "other_data": other_data or {}}
            with self.session_file.open("w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            # 更新缓存
            self._cached_session = session_data
            self._cache_time = time.time()

            return True
        except Exception as e:
            print(f"保存会话数据失败: {e}")
            return False

    def load_session(self, force_reload: bool = False) -> dict[str, Any] | None:
        """
        加载会话数据（带缓存）

        Args:
            force_reload: 是否强制重新加载，忽略缓存

        Returns:
            会话数据字典，失败返回None
        """
        try:
            # 检查缓存是否有效
            if not force_reload and self._cached_session is not None:
                cache_age = time.time() - self._cache_time
                if cache_age < self._cache_ttl:
                    return self._cached_session

            # 缓存失效或强制重新加载
            if not self.session_file.exists():
                self._cached_session = None
                return None

            with self.session_file.open(encoding="utf-8") as f:
                session_data = cast(dict[str, Any], json.load(f))

            # 更新缓存
            self._cached_session = session_data
            self._cache_time = time.time()

            return session_data
        except Exception as e:
            print(f"加载会话数据失败: {e}")
            self._cached_session = None
            return None

    def clear_session(self) -> bool:
        """
        清除会话数据

        Returns:
            是否清除成功
        """
        try:
            if self.session_file.exists():
                self.session_file.unlink()

            # 清除缓存
            self._cached_session = None
            self._cache_time = 0

            return True
        except Exception as e:
            print(f"清除会话数据失败: {e}")
            return False

    def invalidate_cache(self):
        """
        使缓存失效（强制下次加载时重新读取文件）
        """
        self._cached_session = None
        self._cache_time = 0

    def is_session_valid(self) -> bool:
        """
        检查会话是否有效

        Returns:
            会话是否有效
        """
        session_data = self.load_session()
        if not session_data:
            return False

        # 检查必要字段
        return "cookies" in session_data and bool(session_data["cookies"])

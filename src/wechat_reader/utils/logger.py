"""日志工具"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_module_logger(module_name: str) -> logging.Logger:
    """
    获取模块专用的logger

    Args:
        module_name: 模块名称（通常使用 __name__）

    Returns:
        配置好的logger
    """
    logger = logging.getLogger(module_name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    logger.setLevel(logging.INFO)

    # 不传播到父logger，避免重复输出
    logger.propagate = False

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s:%(lineno)d %(message)s"
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def setup_logger(
    name: str, log_file: str | None = None, level: str = "INFO"
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件名（可选）
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    log_level = getattr(logging, level.upper())
    logger.setLevel(log_level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s:%(lineno)d %(message)s"
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        file_path = log_dir / log_file
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

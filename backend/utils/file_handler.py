"""
文件处理工具模块
提供文件读写、验证等辅助功能
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Optional

from config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE

logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """
    计算文件的哈希值

    Args:
        file_path: 文件路径
        algorithm: 哈希算法（md5/sha256）

    Returns:
        哈希字符串
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def safe_filename(filename: str) -> str:
    """
    生成安全的文件名

    Args:
        filename: 原始文件名

    Returns:
        安全的文件名
    """
    # 移除路径分隔符和非法字符
    name = Path(filename).name
    # 替换非ASCII字符
    safe_name = "".join(c for c in name if c.isalnum() or c in "._-() ")
    if not safe_name:
        safe_name = "unnamed_file"
    return safe_name


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名（小写）

    Args:
        filename: 文件名

    Returns:
        小写扩展名（含点号）
    """
    return Path(filename).suffix.lower()


def validate_upload_file(filename: str, file_size: int) -> Tuple[bool, str]:
    """
    验证上传文件是否合规

    Args:
        filename: 文件名
        file_size: 文件大小（字节）

    Returns:
        (是否有效, 消息)
    """
    ext = get_file_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件格式: {ext}，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"

    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        return False, f"文件大小({file_size / (1024*1024):.1f}MB)超过限制({max_mb:.0f}MB)"

    return True, "文件验证通过"


def cleanup_old_files(max_age_hours: int = 24) -> int:
    """
    清理超过指定时间的临时文件

    Args:
        max_age_hours: 最大保留时间（小时）

    Returns:
        清理的文件数量
    """
    import time
    cleaned = 0
    now = time.time()
    max_age_seconds = max_age_hours * 3600

    if not UPLOAD_DIR.exists():
        return 0

    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            file_age = now - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    cleaned += 1
                    logger.info(f"清理过期文件: {file_path.name}")
                except Exception as e:
                    logger.warning(f"清理文件失败: {file_path.name}, 错误: {str(e)}")

    return cleaned


def get_file_size_str(size_bytes: int) -> str:
    """
    将文件大小转换为人类可读格式

    Args:
        size_bytes: 字节数

    Returns:
        格式化的文件大小字符串
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

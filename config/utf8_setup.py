"""
UTF-8 输出工具
安全地设置 stdout/stderr 为 UTF-8 编码。
仅在直接运行脚本时生效，不影响 pytest 等测试框架。
"""

import sys
import io
import os


def ensure_utf8_output():
    """
    确保 stdout/stderr 使用 UTF-8 编码输出。
    在 pytest 等测试框架中自动跳过（因为 pytest 会接管 stdout）。
    """
    # 如果是 pytest 环境，跳过
    if "pytest" in sys.modules:
        return

    # 如果 stdout 已经是 TextIOWrapper 且有 buffer 属性
    try:
        if hasattr(sys.stdout, 'buffer') and getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and getattr(sys.stderr, 'encoding', '').lower() != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # 静默失败，不影响主流程


# 设置环境变量确保 Python 内部使用 UTF-8
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

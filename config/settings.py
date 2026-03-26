"""
全局配置模块
从 .env 文件读取环境变量，定义全局参数。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 加载 .env 文件
load_dotenv(PROJECT_ROOT / ".env")

# ============ Claude API 配置 ============
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")  # 自定义 API 端点，留空则用官方默认
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))

# ============ 数据采集参数 ============
DEFAULT_KLINE_PERIOD = os.getenv("DEFAULT_KLINE_PERIOD", "daily")
NEWS_FETCH_LIMIT = int(os.getenv("NEWS_FETCH_LIMIT", "50"))
HISTORY_REPORT_LIMIT = int(os.getenv("HISTORY_REPORT_LIMIT", "10"))

# ============ 数据库配置 ============
DATABASE_PATH = PROJECT_ROOT / "storage" / "reports.db"

# ============ 关注股票白名单 ============
import json

WATCHLIST_FILE = PROJECT_ROOT / "storage" / "watchlist.json"
DEFAULT_WATCHLIST = {
    "600519": "贵州茅台",
    "300750": "宁德时代",
    "601318": "中国平安",
    "000858": "五粮液",
    "002594": "比亚迪",
    "600036": "招商银行",
    "601012": "隆基绿能",
    "000001": "平安银行",
    "600900": "长江电力",
    "002475": "立讯精密",
}

if WATCHLIST_FILE.exists():
    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            WATCHLIST = json.load(f)
    except Exception:
        WATCHLIST = DEFAULT_WATCHLIST.copy()
else:
    WATCHLIST = DEFAULT_WATCHLIST.copy()
    try:
        WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(WATCHLIST, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

# ============ K 线周期映射 ============
KLINE_PERIODS = {
    "daily": 101,     # 日K
    "weekly": 102,    # 周K
    "monthly": 103,   # 月K
}


def validate_config() -> list[str]:
    """校验配置完整性，返回缺失配置的错误列表。"""
    errors = []
    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY 未配置，请在 .env 文件中设置")
    if not WATCHLIST:
        errors.append("WATCHLIST 关注股票列表为空")
    return errors

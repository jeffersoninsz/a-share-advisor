"""
数据聚合器
合并 AKShare 和 efinance 多源数据为统一格式的市场快照。
"""

from config.settings import WATCHLIST
from data.fetcher_akshare import (
    get_news_feed,
    get_macro_data,
    get_sector_flow,
    get_north_flow,
)
from data.fetcher_efinance import (
    get_realtime_quotes,
    get_kline_summary,
)


def build_market_snapshot() -> dict:
    """
    构建完整的市场快照，聚合多个数据源。

    Returns:
        包含行情、K线摘要、新闻、宏观、板块、北向资金的字典
    """
    symbols = list(WATCHLIST.keys())

    snapshot = {
        "watchlist": WATCHLIST,
        "realtime_quotes": get_realtime_quotes(symbols),
        "kline_summaries": [
            get_kline_summary(symbol, name)
            for symbol, name in WATCHLIST.items()
        ],
        "news": get_news_feed(limit=30),
        "macro": get_macro_data(),
        "sectors": get_sector_flow(top_n=10),
        "north_flow": get_north_flow(),
    }

    return snapshot


def build_minimal_snapshot() -> dict:
    """
    构建最小化市场快照（仅行情和新闻，用于快速预览）。

    Returns:
        精简版市场快照
    """
    symbols = list(WATCHLIST.keys())

    return {
        "watchlist": WATCHLIST,
        "realtime_quotes": get_realtime_quotes(symbols),
        "news": get_news_feed(limit=10),
    }

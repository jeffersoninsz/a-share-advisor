"""
Agent 工具定义
将 data/ 模块的函数注册为 Claude Tool Use 格式。
每个工具包含 name、description、input_schema，供 Claude 自主调用。
"""

import json
from config.settings import WATCHLIST, HISTORY_REPORT_LIMIT
from data.fetcher_akshare import (
    get_news_feed,
    get_macro_data,
    get_sector_flow,
    get_north_flow,
)
from data.fetcher_efinance import (
    get_realtime_quotes,
    get_kline_data,
    get_kline_summary,
)
from storage.database import get_history_reports


# ============ Claude Tool Use 工具定义 ============

TOOL_DEFINITIONS = [
    {
        "name": "get_stock_list",
        "description": "获取当前关注的 A 股股票白名单列表，返回股票代码和名称的映射。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_realtime_quotes",
        "description": "获取指定 A 股股票的实时行情报价，包括最新价、涨跌幅、成交量等。",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "股票代码列表，如 ['600519', '300750']",
                }
            },
            "required": ["symbols"],
        },
    },
    {
        "name": "get_kline_data",
        "description": "获取指定股票的 K 线历史数据（日K/周K/月K），包含开高低收和成交量。",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，如 '600519'",
                },
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "K 线周期：daily(日K)、weekly(周K)、monthly(月K)",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回最近 N 根 K 线，默认 60",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_kline_summary",
        "description": "获取指定股票的 K 线技术摘要，包括 MA5/MA20 均线、近5日/20日涨跌幅等概览信息。比 get_kline_data 更精简。",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码",
                },
                "name": {
                    "type": "string",
                    "description": "股票名称",
                },
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "K 线周期，默认 daily",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_news_feed",
        "description": "获取财联社 7x24 实时财经快讯，包含标题、内容、发布时间。",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "拉取条数，默认 50",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_macro_data",
        "description": "获取中国宏观经济指标（CPI 同比、制造业 PMI 等）的最新数据。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_sector_flow",
        "description": "获取 A 股行业板块资金流向排名，包括板块名称和涨跌幅。",
        "input_schema": {
            "type": "object",
            "properties": {
                "top_n": {
                    "type": "integer",
                    "description": "返回前 N 个板块，默认 10",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_north_flow",
        "description": "获取沪深港通北向资金（外资）最新净流入数据。",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_history_reports",
        "description": "获取历史分析推荐报告列表，用于复盘过往推荐与评估准确率。",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "返回条数，默认 10",
                }
            },
            "required": [],
        },
    },
]


# ============ 工具执行分发 ============

def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    """
    根据工具名称和输入参数，执行对应的工具函数并返回 JSON 字符串结果。

    Args:
        tool_name: 工具名称
        tool_input: 工具输入参数字典

    Returns:
        工具执行结果的 JSON 字符串
    """
    try:
        if tool_name == "get_stock_list":
            result = WATCHLIST

        elif tool_name == "get_realtime_quotes":
            symbols = tool_input.get("symbols", list(WATCHLIST.keys()))
            result = get_realtime_quotes(symbols)

        elif tool_name == "get_kline_data":
            symbol = tool_input["symbol"]
            period = tool_input.get("period", "daily")
            limit = tool_input.get("limit", 60)
            result = get_kline_data(symbol, period, limit)

        elif tool_name == "get_kline_summary":
            symbol = tool_input["symbol"]
            name = tool_input.get("name", "")
            period = tool_input.get("period", "daily")
            result = get_kline_summary(symbol, name, period)

        elif tool_name == "get_news_feed":
            limit = tool_input.get("limit", 50)
            result = get_news_feed(limit)

        elif tool_name == "get_macro_data":
            result = get_macro_data()

        elif tool_name == "get_sector_flow":
            top_n = tool_input.get("top_n", 10)
            result = get_sector_flow(top_n)

        elif tool_name == "get_north_flow":
            result = get_north_flow()

        elif tool_name == "get_history_reports":
            limit = tool_input.get("limit", HISTORY_REPORT_LIMIT)
            result = get_history_reports(limit)

        else:
            result = {"error": f"未知工具: {tool_name}"}

        return json.dumps(result, ensure_ascii=False, default=str)

    except Exception as e:
        return json.dumps(
            {"error": f"工具 {tool_name} 执行失败: {str(e)}"},
            ensure_ascii=False,
        )

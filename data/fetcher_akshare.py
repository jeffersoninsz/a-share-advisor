"""
AKShare 数据采集模块
负责从 AKShare 获取：财联社7x24快讯、宏观经济数据、板块资金流向、北向资金。
"""

from datetime import datetime
from typing import Optional

import akshare as ak
import pandas as pd


def get_news_feed(limit: int = 50) -> list[dict]:
    """
    获取财联社 7x24 实时快讯。

    Args:
        limit: 拉取条数，默认 50

    Returns:
        快讯列表，每条包含 title, content, datetime 等字段
    """
    try:
        df = ak.stock_zh_a_alerts_cls()
        if df is None or df.empty:
            return []
        # 取最新 limit 条
        df = df.head(limit)
        records = []
        for _, row in df.iterrows():
            records.append({
                "title": str(row.get("标题", "")),
                "content": str(row.get("内容", "")),
                "datetime": str(row.get("发布时间", "")),
                "source": "财联社7x24",
            })
        return records
    except Exception as e:
        return [{"error": f"获取财联社快讯失败: {str(e)}", "source": "财联社7x24"}]


def get_macro_cpi() -> dict:
    """获取中国 CPI 最新数据。"""
    try:
        df = ak.macro_china_cpi_yearly()
        if df is None or df.empty:
            return {"error": "CPI 数据为空"}
        latest = df.iloc[-1]
        return {
            "indicator": "CPI 同比",
            "date": str(latest.get("日期", "")),
            "value": str(latest.get("今值", "")),
            "source": "AKShare 宏观数据",
        }
    except Exception as e:
        return {"error": f"获取 CPI 数据失败: {str(e)}"}


def get_macro_pmi() -> dict:
    """获取中国 PMI 最新数据。"""
    try:
        df = ak.macro_china_pmi()
        if df is None or df.empty:
            return {"error": "PMI 数据为空"}
        latest = df.iloc[-1]
        return {
            "indicator": "制造业PMI",
            "date": str(latest.get("日期", "")),
            "value": str(latest.get("今值", "")),
            "source": "AKShare 宏观数据",
        }
    except Exception as e:
        return {"error": f"获取 PMI 数据失败: {str(e)}"}


def get_macro_data() -> list[dict]:
    """获取一组宏观经济指标（CPI、PMI 等）。"""
    results = []
    results.append(get_macro_cpi())
    results.append(get_macro_pmi())
    return results


def get_sector_flow(top_n: int = 10) -> list[dict]:
    """
    获取行业板块资金流向排名。

    Args:
        top_n: 返回前 N 个板块

    Returns:
        板块资金流向列表
    """
    try:
        df = ak.stock_board_industry_name_em()
        if df is None or df.empty:
            return [{"error": "板块数据为空"}]
        df = df.head(top_n)
        records = []
        for _, row in df.iterrows():
            records.append({
                "sector": str(row.get("板块名称", "")),
                "change_pct": str(row.get("涨跌幅", "")),
                "source": "AKShare 板块数据",
            })
        return records
    except Exception as e:
        return [{"error": f"获取板块数据失败: {str(e)}"}]


def get_north_flow() -> dict:
    """获取北向资金（沪深港通）最新净流入数据。"""
    try:
        df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向")
        if df is None or df.empty:
            return {"error": "北向资金数据为空"}
        latest = df.iloc[-1]
        return {
            "indicator": "北向资金净流入",
            "date": str(latest.get("日期", latest.get("date", ""))),
            "value": str(latest.get("当日净流入", latest.get("value", ""))),
            "unit": "亿元",
            "source": "AKShare 北向资金",
        }
    except Exception as e:
        return {"error": f"获取北向资金数据失败: {str(e)}"}

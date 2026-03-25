"""
efinance 数据采集模块
负责从 efinance（东方财富）获取：A 股实时行情报价、K 线历史数据。
"""

from typing import Optional

import efinance as ef
import pandas as pd


def get_realtime_quotes(symbols: list[str]) -> list[dict]:
    """
    获取指定股票的实时行情报价。

    Args:
        symbols: 股票代码列表，如 ["600519", "300750"]

    Returns:
        实时行情列表，每条包含 symbol, name, price, change_pct 等
    """
    try:
        df = ef.stock.get_realtime_quotes(symbols)
        if df is None or df.empty:
            return [{"error": "实时行情数据为空"}]
        records = []
        for _, row in df.iterrows():
            records.append({
                "symbol": str(row.get("股票代码", "")),
                "name": str(row.get("股票名称", "")),
                "price": str(row.get("最新价", "")),
                "change_pct": str(row.get("涨跌幅", "")),
                "change_amount": str(row.get("涨跌额", "")),
                "volume": str(row.get("成交量", "")),
                "turnover": str(row.get("成交额", "")),
                "high": str(row.get("最高", "")),
                "low": str(row.get("最低", "")),
                "open": str(row.get("今开", "")),
                "prev_close": str(row.get("昨收", "")),
                "source": "efinance 实时行情",
            })
        return records
    except Exception as e:
        return [{"error": f"获取实时行情失败: {str(e)}", "source": "efinance"}]


def get_kline_data(
    symbol: str,
    period: str = "daily",
    limit: int = 60
) -> list[dict]:
    """
    获取指定股票的 K 线历史数据。

    Args:
        symbol: 股票代码，如 "600519"
        period: 周期，"daily"(日K) / "weekly"(周K) / "monthly"(月K)
        limit: 返回最近 N 根 K 线，默认 60

    Returns:
        K 线数据列表
    """
    # efinance K 线类型映射
    klt_map = {
        "daily": 101,
        "weekly": 102,
        "monthly": 103,
    }
    klt = klt_map.get(period, 101)

    try:
        df = ef.stock.get_quote_history(symbol, klt=klt)
        if df is None or df.empty:
            return [{"error": f"K线数据为空: {symbol}"}]
        # 取最近 limit 根
        df = df.tail(limit)
        records = []
        for _, row in df.iterrows():
            records.append({
                "date": str(row.get("日期", "")),
                "open": str(row.get("开盘", "")),
                "close": str(row.get("收盘", "")),
                "high": str(row.get("最高", "")),
                "low": str(row.get("最低", "")),
                "volume": str(row.get("成交量", "")),
                "turnover": str(row.get("成交额", "")),
                "change_pct": str(row.get("涨跌幅", "")),
                "source": f"efinance {symbol} K线",
            })
        return records
    except Exception as e:
        return [{"error": f"获取 K 线数据失败({symbol}): {str(e)}"}]


def get_kline_summary(symbol: str, name: str = "", period: str = "daily") -> dict:
    """
    获取指定股票的 K 线摘要信息（近期趋势概览）。

    Args:
        symbol: 股票代码
        name: 股票名称
        period: K 线周期

    Returns:
        K 线摘要字典
    """
    klines = get_kline_data(symbol, period, limit=30)
    if not klines or "error" in klines[0]:
        return {"symbol": symbol, "name": name, "error": klines[0].get("error", "未知错误")}

    # 计算简单指标
    closes = [float(k["close"]) for k in klines if k.get("close")]
    if not closes:
        return {"symbol": symbol, "name": name, "error": "无有效收盘价"}

    latest_price = closes[-1]
    ma5 = sum(closes[-5:]) / min(len(closes), 5) if len(closes) >= 5 else latest_price
    ma20 = sum(closes[-20:]) / min(len(closes), 20) if len(closes) >= 20 else latest_price
    price_change_5d = ((closes[-1] - closes[-6]) / closes[-6] * 100) if len(closes) >= 6 else 0
    price_change_20d = ((closes[-1] - closes[-21]) / closes[-21] * 100) if len(closes) >= 21 else 0

    return {
        "symbol": symbol,
        "name": name,
        "latest_price": round(latest_price, 2),
        "ma5": round(ma5, 2),
        "ma20": round(ma20, 2),
        "price_above_ma5": latest_price > ma5,
        "price_above_ma20": latest_price > ma20,
        "change_5d_pct": round(price_change_5d, 2),
        "change_20d_pct": round(price_change_20d, 2),
        "data_points": len(klines),
        "source": f"efinance {symbol} K线摘要",
    }

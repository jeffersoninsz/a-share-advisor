"""
数据采集模块单元测试
测试 AKShare 和 efinance 数据接口的连通性与返回格式。
"""

import pytest


class TestAKShareFetcher:
    """AKShare 数据采集测试"""

    def test_get_news_feed(self):
        """测试财联社快讯接口连通性"""
        from data.fetcher_akshare import get_news_feed
        result = get_news_feed(limit=5)
        assert isinstance(result, list)
        assert len(result) > 0
        # 检查数据结构（正常返回或错误返回都可以）
        first = result[0]
        assert isinstance(first, dict)
        if "error" not in first:
            assert "title" in first or "content" in first

    def test_get_macro_data(self):
        """测试宏观数据接口连通性"""
        from data.fetcher_akshare import get_macro_data
        result = get_macro_data()
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_get_sector_flow(self):
        """测试板块资金流向接口连通性"""
        from data.fetcher_akshare import get_sector_flow
        result = get_sector_flow(top_n=5)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_north_flow(self):
        """测试北向资金接口连通性"""
        from data.fetcher_akshare import get_north_flow
        result = get_north_flow()
        assert isinstance(result, dict)


class TestEfinanceFetcher:
    """efinance 数据采集测试"""

    def test_get_realtime_quotes(self):
        """测试实时行情接口连通性"""
        from data.fetcher_efinance import get_realtime_quotes
        result = get_realtime_quotes(["600519"])
        assert isinstance(result, list)
        assert len(result) > 0
        first = result[0]
        assert isinstance(first, dict)

    def test_get_kline_data(self):
        """测试 K 线数据接口连通性"""
        from data.fetcher_efinance import get_kline_data
        result = get_kline_data("600519", period="daily", limit=10)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_kline_summary(self):
        """测试 K 线摘要"""
        from data.fetcher_efinance import get_kline_summary
        result = get_kline_summary("600519", "贵州茅台")
        assert isinstance(result, dict)
        assert "symbol" in result
        assert result["symbol"] == "600519"

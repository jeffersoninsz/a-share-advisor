"""
数据库操作单元测试
使用临时数据库测试 SQLite CRUD 操作。
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from storage.models import AnalysisReport, Recommendation


@pytest.fixture(autouse=True)
def temp_database():
    """为每个测试创建临时数据库文件。"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)

    # 覆盖 DATABASE_PATH 为临时路径
    with patch("storage.database.DATABASE_PATH", temp_path):
        from storage.database import init_db
        init_db()
        yield temp_path

    # 清理
    if temp_path.exists():
        temp_path.unlink()


def _make_sample_report() -> AnalysisReport:
    """创建一个样本分析报告。"""
    return AnalysisReport(
        timestamp="2026-03-25T16:00:00+08:00",
        market_summary="测试市场概况",
        recommendations=[
            Recommendation(
                symbol="600519",
                name="贵州茅台",
                action="BUY",
                confidence="HIGH",
                reason="测试推荐理由",
                analysis_process=["步骤1", "步骤2"],
                data_sources=["数据来源1"],
                risk_note="测试风险提示",
            )
        ],
    )


class TestDatabase:
    """数据库操作测试"""

    def test_save_and_get_report(self, temp_database):
        """测试保存和查询报告"""
        with patch("storage.database.DATABASE_PATH", temp_database):
            from storage.database import save_report, get_history_reports

            report = _make_sample_report()
            report_id = save_report(report)
            assert report_id > 0

            history = get_history_reports(limit=5)
            assert len(history) == 1
            assert history[0]["id"] == report_id
            assert history[0]["market_summary"] == "测试市场概况"

    def test_get_report_by_id(self, temp_database):
        """测试按 ID 查询报告"""
        with patch("storage.database.DATABASE_PATH", temp_database):
            from storage.database import save_report, get_report_by_id

            report = _make_sample_report()
            report_id = save_report(report)

            result = get_report_by_id(report_id)
            assert result is not None
            assert result["id"] == report_id

            # 不存在的 ID
            result = get_report_by_id(99999)
            assert result is None

    def test_accuracy_tracking(self, temp_database):
        """测试准确率追踪"""
        with patch("storage.database.DATABASE_PATH", temp_database):
            from storage.database import (
                save_report,
                update_accuracy,
                get_accuracy_stats,
                get_accuracy_records,
            )

            report = _make_sample_report()
            save_report(report)

            # 查看初始状态
            stats = get_accuracy_stats()
            assert stats["total"] == 1
            assert stats["pending"] == 1

            # 标记结果
            records = get_accuracy_records()
            assert len(records) == 1
            update_accuracy(records[0]["id"], "WIN")

            # 重新统计
            stats = get_accuracy_stats()
            assert stats["wins"] == 1
            assert stats["win_rate"] == 100.0

    def test_update_accuracy_invalid(self, temp_database):
        """测试无效的准确率更新"""
        with patch("storage.database.DATABASE_PATH", temp_database):
            from storage.database import update_accuracy

            result = update_accuracy(1, "INVALID_VALUE")
            assert result is False

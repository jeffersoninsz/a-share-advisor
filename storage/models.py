"""
数据模型定义
使用 Pydantic 定义推荐记录和分析日志的数据结构。
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    """单个推荐记录"""
    symbol: str = Field(description="股票代码，如 600519")
    name: str = Field(description="股票名称，如 贵州茅台")
    action: str = Field(description="推荐操作: BUY / SELL / HOLD")
    confidence: str = Field(description="置信度: HIGH / MEDIUM / LOW")
    reason: str = Field(description="推荐理由概述")
    analysis_process: list[str] = Field(
        default_factory=list,
        description="逐步分析过程"
    )
    data_sources: list[str] = Field(
        default_factory=list,
        description="数据来源列表"
    )
    risk_note: str = Field(default="", description="风险提示")


class AnalysisReport(BaseModel):
    """完整分析报告"""
    timestamp: str = Field(description="分析时间 ISO 8601 格式")
    market_summary: str = Field(default="", description="市场整体概况")
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="推荐列表"
    )
    watchlist_updates: list[dict] = Field(
        default_factory=list,
        description="自选股状态更新"
    )


class ReportRecord(BaseModel):
    """数据库中的报告记录"""
    id: Optional[int] = None
    timestamp: str
    market_summary: str = ""
    report_json: str = Field(description="完整报告 JSON 字符串")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )


class AccuracyRecord(BaseModel):
    """推荐准确率记录"""
    id: Optional[int] = None
    report_id: int
    symbol: str
    name: str
    action: str
    confidence: str
    actual_result: Optional[str] = Field(
        default=None,
        description="实际结果: WIN / LOSE / PENDING"
    )
    marked_at: Optional[str] = None

"""
Agent I/O Schema 定义
使用 Pydantic 定义 Agent 输入输出的数据结构，复用 storage.models 的核心模型。
"""

from storage.models import AnalysisReport, Recommendation

# 直接复用 storage.models 中的定义
# AnalysisReport 即为 Agent 的最终输出格式
# Recommendation 即为单条推荐的格式

# Agent 输出的 JSON Schema（用于 Claude Tool Use 的 output 校验）
REPORT_JSON_SCHEMA = AnalysisReport.model_json_schema()

__all__ = ["AnalysisReport", "Recommendation", "REPORT_JSON_SCHEMA"]

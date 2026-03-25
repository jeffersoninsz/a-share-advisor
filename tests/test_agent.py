"""
Agent 逻辑测试
测试 Prompt 构建、工具分发、JSON 解析等核心逻辑。
"""

import json
import pytest

from agent.prompts import build_system_prompt
from agent.tools import TOOL_DEFINITIONS, dispatch_tool
from agent.schemas import AnalysisReport, Recommendation


class TestPrompts:
    """Prompt 模板测试"""

    def test_build_system_prompt(self):
        """测试 System Prompt 构建"""
        prompt = build_system_prompt("2026-03-25T16:00:00+08:00")
        assert "Alpha Advisor" in prompt
        assert "A 股" in prompt
        assert "2026-03-25" in prompt
        assert "BUY" in prompt
        assert "analysis_process" in prompt

    def test_system_prompt_contains_rules(self):
        """测试 System Prompt 包含核心规则"""
        prompt = build_system_prompt("2026-01-01T00:00:00+08:00")
        assert "只分析不执行" in prompt
        assert "仅限 A 股" in prompt
        assert "风险提示" in prompt


class TestToolDefinitions:
    """工具定义测试"""

    def test_tool_count(self):
        """测试工具数量"""
        assert len(TOOL_DEFINITIONS) == 9

    def test_tool_structure(self):
        """测试每个工具定义的结构完整性"""
        required_keys = {"name", "description", "input_schema"}
        for tool in TOOL_DEFINITIONS:
            assert required_keys.issubset(tool.keys()), f"工具 {tool.get('name')} 缺少必要字段"
            assert isinstance(tool["input_schema"], dict)
            assert "type" in tool["input_schema"]

    def test_tool_names_unique(self):
        """测试工具名称唯一性"""
        names = [t["name"] for t in TOOL_DEFINITIONS]
        assert len(names) == len(set(names)), "存在重复的工具名称"


class TestToolDispatch:
    """工具分发测试"""

    def test_get_stock_list(self):
        """测试股票列表工具"""
        result = dispatch_tool("get_stock_list", {})
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "600519" in data  # 贵州茅台应在白名单中

    def test_unknown_tool(self):
        """测试未知工具名"""
        result = dispatch_tool("nonexistent_tool", {})
        data = json.loads(result)
        assert "error" in data


class TestSchemas:
    """Schema 校验测试"""

    def test_recommendation_valid(self):
        """测试有效的推荐记录"""
        rec = Recommendation(
            symbol="600519",
            name="贵州茅台",
            action="BUY",
            confidence="HIGH",
            reason="测试理由",
            analysis_process=["步骤1", "步骤2"],
            data_sources=["数据来源1"],
            risk_note="测试风险",
        )
        assert rec.symbol == "600519"
        assert rec.action == "BUY"

    def test_analysis_report_valid(self):
        """测试有效的分析报告"""
        report = AnalysisReport(
            timestamp="2026-03-25T16:00:00+08:00",
            market_summary="测试概况",
            recommendations=[
                Recommendation(
                    symbol="600519",
                    name="贵州茅台",
                    action="BUY",
                    confidence="HIGH",
                    reason="测试",
                    risk_note="注意风险",
                )
            ],
        )
        assert len(report.recommendations) == 1
        # 测试 JSON 序列化
        json_str = report.model_dump_json(ensure_ascii=False)
        assert "贵州茅台" in json_str


class TestReportExtraction:
    """JSON 报告提取测试"""

    def test_extract_pure_json(self):
        """测试纯 JSON 提取"""
        from agent.brain import _extract_report
        text = '{"timestamp": "2026-01-01", "market_summary": "test"}'
        result = _extract_report(text)
        assert result is not None
        assert result["market_summary"] == "test"

    def test_extract_from_markdown(self):
        """测试从 Markdown 代码块提取"""
        from agent.brain import _extract_report
        text = '''这是分析结果：

```json
{"timestamp": "2026-01-01", "market_summary": "test"}
```

以上是报告。'''
        result = _extract_report(text)
        assert result is not None
        assert result["timestamp"] == "2026-01-01"

    def test_extract_from_mixed_text(self):
        """测试从混合文本提取"""
        from agent.brain import _extract_report
        text = '前面有文字 {"timestamp": "2026-01-01", "market_summary": "test"} 后面也有'
        result = _extract_report(text)
        assert result is not None

    def test_extract_empty(self):
        """测试空输入"""
        from agent.brain import _extract_report
        assert _extract_report("") is None
        assert _extract_report(None) is None

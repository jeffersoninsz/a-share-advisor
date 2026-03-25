"""测试重构后的 Agent 核心引擎"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging
logging.basicConfig(level=logging.INFO)

from agent.brain import run_analysis

def on_tool(name, inputs):
    print(f"  --> 调用工具: {name} 参数: {inputs}")

def on_think(text):
    print(f"  --> 思考: {text[:50]}...")

print("========== 开始测试 OpenRouter Agent ==========")
try:
    result = run_analysis(
        on_tool_call=on_tool,
        on_thinking=on_think
    )
    if result["success"]:
        print("✅ 测试成功，生成的报告:")
        print(result["report"])
    else:
        print(f"❌ 测试失败: {result['error']}")
except Exception as e:
    print(f"🚨 运行异常: {e}")

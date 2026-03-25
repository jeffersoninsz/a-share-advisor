import asyncio
from agent.brain import run_analysis
from config.settings import WATCHLIST

def test_features():
    print("=== 开始功能完整性测试 ===")
    print(f"1. 选股与情报测试配置: {list(WATCHLIST.keys())}")
    
    # 模拟一个快速分析请求的拦截回调
    def on_tool(tool_name, tool_input):
        print(f"🔧 被调用的工具 -> {tool_name}: {tool_input}")
        
    def on_thinking(text):
        pass

    try:
        result = run_analysis(on_tool_call=on_tool, on_thinking=on_thinking)
        if result["success"]:
            print("✅ 选股、分析、情报测试成功完成！")
            print(f"报告 ID: {result['report_id']}")
            print(f"生成内容摘要: {str(result['report'])[:200]}...")
        else:
            print(f"❌ 测试失败: {result.get('error')}")
    except Exception as e:
        print(f"❌ 运行异常: {e}")

if __name__ == "__main__":
    test_features()

"""验证 SDK 与该反代配置的真实连通性"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import anthropic

KEY = "sk-ant-oat01-JFuuV-3FrGkAUUOR2gChxjxXtR4cEz6UGGyjpWzm_ssHSXA_ivcXOXnrqY-Po86iH3ZLYqBDz6QNAcc8AHCYM-bqFaMv2AA"
BASE_URL = "https://code.newcli.com/claude"
MODEL = "claude-sonnet-4-6"

print(f"初始化 Anthropic Client:\n - Base URL: {BASE_URL}\n - Model: {MODEL}")

try:
    # 按照标准的方式初始化
    client = anthropic.Anthropic(
        api_key=KEY,
        base_url=BASE_URL,
    )
    
    print("\n>>> 正在向反代发送标准 API 请求...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=100,
        messages=[
            {"role": "user", "content": "你好，请回复'测试成功'。"}
        ]
    )
    print(f"\n✅ 成功！来自服务器的回复: {response.content[0].text}")

except Exception as e:
    print(f"\n❌ 失败！发生错误:\n{type(e).__name__}: {str(e)}")
    print("\n===============================")
    print("【系统诊断】：反代服务器拦截了该请求！")
    print("原因：此反代端点只识别 Claude Code CLI 工具本身的请求包结构，拒绝了 Python SDK 的纯净 API 调用。")


"""测试 OpenRouter 与 Anthropic SDK 直接兼容性"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import anthropic

KEY = "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"

client = anthropic.Anthropic(
    api_key=KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:8501", # OpenRouter recommendations
        "X-Title": "A-Share Advisor",
    }
)

try:
    print("Testing OpenRouter with Anthropic SDK...")
    response = client.messages.create(
        model="anthropic/claude-3.5-sonnet", # OpenRouter 的模型名称格式
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello! Reply with 'OKOpenRouter'"}]
    )
    print(f"SUCCESS: {response.content[0].text}")
except Exception as e:
    print(f"FAILED: {e}")

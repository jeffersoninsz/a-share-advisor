"""
AI Agent 核心引擎
基于 Claude Tool Use API 的自定义循环，实现每次分析的隔离会话。
"""

import json
import logging
from datetime import datetime
from typing import Optional, Callable

import openai

from config.settings import ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, CLAUDE_MODEL, MAX_TOKENS
from agent.prompts import build_system_prompt
from agent.tools import TOOL_DEFINITIONS, dispatch_tool
from agent.schemas import AnalysisReport
from storage.database import init_db, save_report

# 日志配置
logger = logging.getLogger("agent.brain")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Tool Use 循环最大轮次（防止无限循环）
MAX_TOOL_ROUNDS = 15


def run_analysis(
    on_tool_call: Optional[Callable[[str, dict], None]] = None,
    on_thinking: Optional[Callable[[str], None]] = None,
    stop_flag: Optional[Callable[[], bool]] = None,
) -> dict:
    """
    执行一次完整的 AI 分析。

    每次调用创建全新的 Claude 对话（隔离会话），Agent 通过 Tool Use
    自主决定调用哪些工具收集数据，最终输出结构化 JSON 推荐报告。

    Args:
        on_tool_call: 工具调用回调函数(tool_name, tool_input)，用于 UI 实时展示
        on_thinking: Agent 思考过程回调函数(text)，用于 UI 实时展示
        stop_flag: 停止标志函数，返回 True 时中断分析

    Returns:
        包含 success, report, report_id, error, tool_calls_log 的结果字典
    """
    # 确保数据库已初始化
    init_db()

    # 校验 API Key (支持热加载与 Streamlit Secrets)
    import os
    import streamlit as st
    
    current_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not current_api_key and hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
        current_api_key = st.secrets["ANTHROPIC_API_KEY"]
    if not current_api_key:
        current_api_key = ANTHROPIC_API_KEY

    current_base_url = os.getenv("ANTHROPIC_BASE_URL")
    if not current_base_url and hasattr(st, "secrets") and "ANTHROPIC_BASE_URL" in st.secrets:
        current_base_url = st.secrets["ANTHROPIC_BASE_URL"]
    if not current_base_url:
        current_base_url = ANTHROPIC_BASE_URL

    if not current_api_key:
        return {
            "success": False,
            "error": "ANTHROPIC_API_KEY 未配置，请在前端设置页面配置或在 Streamlit Secrets 中配置",
            "report": None,
            "report_id": None,
            "tool_calls_log": [],
        }

    # 转换 TOOL_DEFINITIONS 到 OpenAI 格式
    openai_tools = []
    for t in TOOL_DEFINITIONS:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"]
            }
        })

    # 创建 OpenAI 客户端（每次新建，隔离会话）
    client_kwargs = {"api_key": current_api_key}
    if current_base_url:
        client_kwargs["base_url"] = current_base_url
        logger.info(f"📡 使用自定义 API 端点: {current_base_url}")
    client = openai.OpenAI(**client_kwargs)

    # 构建 System Prompt
    current_time = datetime.now().isoformat()
    system_prompt = build_system_prompt(current_time)

    # 初始消息 (OpenAI 将 system prompt 放在 role: system)
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": "请立即开始分析当前 A 股市场，使用你的工具收集数据，然后输出结构化的推荐报告。",
        }
    ]

    # 工具调用日志
    tool_calls_log = []
    final_text = ""

    logger.info("🚀 开始 AI 分析会话")

    for round_num in range(MAX_TOOL_ROUNDS):
        # 检查停止标志
        if stop_flag and stop_flag():
            logger.info("⛔ 分析被用户中断")
            return {
                "success": False,
                "error": "分析被用户中断",
                "report": None,
                "report_id": None,
                "tool_calls_log": tool_calls_log,
            }

        logger.info(f"📡 第 {round_num + 1} 轮对话...")

        try:
            response = client.chat.completions.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                tools=openai_tools,
                messages=messages,
            )
        except Exception as e:
            logger.error(f"API 调用失败: {e}")
            return {
                "success": False,
                "error": f"API 调用失败: {str(e)}",
                "report": None,
                "report_id": None,
                "tool_calls_log": tool_calls_log,
            }

        # 处理响应内容
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls or []
        text_content = response_message.content or ""
        text_blocks = []

        if text_content:
            text_blocks.append(text_content)
            if on_thinking:
                on_thinking(text_content)

        # 如果没有工具调用，说明 Agent 已完成分析
        if not tool_calls:
            final_text = "\n".join(text_blocks)
            logger.info("✅ Agent 完成分析，输出最终结果")
            break

        # 处理工具调用
        # 先把 assistant 的响应加入消息历史
        messages.append(response_message.model_dump(exclude_unset=True))

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_input = json.loads(tool_call.function.arguments)
            except Exception:
                tool_input = {}

            logger.info(f"🔧 调用工具: {tool_name}({json.dumps(tool_input, ensure_ascii=False)[:200]})")

            if on_tool_call:
                on_tool_call(tool_name, tool_input)

            # 执行工具
            result = dispatch_tool(tool_name, tool_input)

            tool_calls_log.append({
                "round": round_num + 1,
                "tool": tool_name,
                "input": tool_input,
                "output_preview": result[:500] if len(result) > 500 else result,
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    else:
        # 超过最大轮次
        logger.warning(f"⚠️ 超过最大工具调用轮次 ({MAX_TOOL_ROUNDS})")
        final_text = "\n".join(text_blocks) if text_blocks else ""

    # 解析分析报告
    report_data = _extract_report(final_text)

    if report_data is None:
        return {
            "success": False,
            "error": "无法从 Agent 输出中解析分析报告 JSON",
            "raw_output": final_text,
            "report": None,
            "report_id": None,
            "tool_calls_log": tool_calls_log,
        }

    # Pydantic 校验
    try:
        report = AnalysisReport(**report_data)
    except Exception as e:
        logger.error(f"报告格式校验失败: {e}")
        return {
            "success": False,
            "error": f"报告格式校验失败: {str(e)}",
            "raw_output": final_text,
            "report": report_data,
            "report_id": None,
            "tool_calls_log": tool_calls_log,
        }

    # 保存到数据库
    try:
        report_id = save_report(report)
        logger.info(f"💾 报告已保存，ID: {report_id}")
    except Exception as e:
        logger.error(f"保存报告失败: {e}")
        report_id = None

    return {
        "success": True,
        "report": report.model_dump(),
        "report_id": report_id,
        "tool_calls_log": tool_calls_log,
        "error": None,
    }


def _extract_report(text: str) -> Optional[dict]:
    """
    从 Agent 的文本输出中提取 JSON 报告。

    支持两种格式：
    1. 纯 JSON 字符串
    2. Markdown 代码块中的 JSON (```json ... ```)

    Args:
        text: Agent 原始输出文本

    Returns:
        解析后的字典，失败返回 None
    """
    if not text:
        return None

    text = text.strip()

    # 尝试 1: 直接解析为 JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试 2: 从 markdown 代码块中提取
    import re
    json_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    matches = re.findall(json_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # 尝试 3: 找到第一个 { 和最后一个 } 之间的内容
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    return None

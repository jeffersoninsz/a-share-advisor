"""
A 股 AI 量化分析顾问 — Streamlit Dashboard
系统唯一的前端入口。

启动方式: streamlit run app.py
"""

from config.utf8_setup import ensure_utf8_output
ensure_utf8_output()

import json
import threading
from datetime import datetime

import streamlit as st
import pandas as pd

from config.settings import WATCHLIST, validate_config
from storage.database import (
    init_db,
    get_history_reports,
    get_report_by_id,
    get_accuracy_stats,
    get_accuracy_records,
    update_accuracy,
)
from agent.brain import run_analysis

# ============ 页面配置 ============
st.set_page_config(
    page_title="A股 AI 分析顾问",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ 自定义 CSS (黑金赛博羊皮纸) ============
st.markdown("""
<style>
/* 古典衬线与神秘感字体 */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Noto+Serif+SC:wght@300;400;700&display=swap');

html, body, [class*="st-"] {
    font-family: 'Noto Serif SC', 'Cinzel', serif;
}

/* 全局背景: 暗黑羊皮纸质感 */
.stApp {
    background-color: #0a0908 !important;
    background-image: 
        radial-gradient(circle at 50% 50%, rgba(20, 18, 15, 0.9) 0%, rgba(5, 5, 5, 1) 100%),
        url('data:image/svg+xml;utf8,<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><filter id="noiseFilter"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="4" stitchTiles="stitch"/></filter><rect width="100%" height="100%" filter="url(%23noiseFilter)" opacity="0.03"/></svg>') !important;
    color: #d4c4a8;
}

/* 隐藏 Streamlit 默认的 Header 和 Footer */
header {visibility: hidden;}
footer {visibility: hidden;}

/* 发光标题与文字隔离线 */
h1, h2, h3 {
    text-shadow: 0 0 15px rgba(212, 175, 55, 0.5), 0 0 1px rgba(212, 175, 55, 0.8);
    letter-spacing: 3px;
    font-weight: 400 !important;
    color: #e5c158 !important;
}

h1 {
    text-align: center;
    border-bottom: 1px solid transparent;
    border-image: linear-gradient(to right, transparent, rgba(212,175,55,0.6), transparent) 1;
    padding-bottom: 15px;
    margin-bottom: 30px;
}

/* 卡片容器：深色羊皮纸加金边 */
div[data-testid="metric-container"], 
div[data-testid="stExpander"], 
div[data-baseweb="card"],
.stAlert {
    background: 
        linear-gradient(135deg, rgba(22, 20, 17, 0.95) 0%, rgba(10, 9, 8, 0.98) 100%),
        url('data:image/svg+xml;utf8,<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><filter id="noiseFilter"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch"/></filter><rect width="100%" height="100%" filter="url(%23noiseFilter)" opacity="0.04"/></svg>') !important;
    border: 1px solid rgba(212, 175, 55, 0.4) !important;
    border-radius: 2px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.8), inset 0 0 10px rgba(212,175,55,0.05) !important;
    color: #eaddc5 !important;
    padding: 10px;
}

/* Expander 标题的高级感 */
.streamlit-expanderHeader {
    background-color: transparent !important;
    color: #e5c158 !important;
    border-bottom: 1px solid rgba(212, 175, 55, 0.2) !important;
    font-weight: 600;
    letter-spacing: 1px;
    transition: all 0.3s ease;
}
.streamlit-expanderHeader:hover {
    color: #fff2c8 !important;
    text-shadow: 0 0 10px rgba(212,175,55,0.8);
}

/* 按钮的黑金神秘脉冲效果 */
button[kind="primary"], button[data-testid="baseButton-primary"] {
    background: linear-gradient(45deg, #1f1b13, #0a0908) !important;
    border: 1px solid #d4af37 !important;
    color: #d4af37 !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
    box-shadow: 0 0 15px rgba(212, 175, 55, 0.2), inset 0 0 10px rgba(212, 175, 55, 0.1) !important;
    position: relative;
    overflow: hidden;
}
button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover {
    background: linear-gradient(45deg, #d4af37, #b08d28) !important;
    color: #000 !important;
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.6), 0 0 40px rgba(212, 175, 55, 0.4) !important;
    transform: translateY(-2px);
    text-shadow: none;
    border-color: #fff !important;
}

button[kind="secondary"], button[data-testid="baseButton-secondary"] {
    background: transparent !important;
    border: 1px solid rgba(212, 175, 55, 0.3) !important;
    color: #aa9c80 !important;
    transition: all 0.3s ease;
    letter-spacing: 1px;
}
button[kind="secondary"]:hover, button[data-testid="baseButton-secondary"]:hover {
    border-color: #d4af37 !important;
    box-shadow: 0 0 15px rgba(212, 175, 55, 0.4);
    color: #e5c158 !important;
    transform: translateY(-1px);
}

/* 侧边栏的深层质感 */
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(212, 175, 55, 0.3) !important;
    background: 
        linear-gradient(180deg, rgba(10,9,8,1) 0%, rgba(15,13,11,1) 100%),
        url('data:image/svg+xml;utf8,<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"><filter id="noiseFilter"><feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" stitchTiles="stitch"/></filter><rect width="100%" height="100%" filter="url(%23noiseFilter)" opacity="0.05"/></svg>') !important;
    box-shadow: inset -10px 0 20px rgba(0,0,0,0.9);
}

/* 分割线鎏金效果 */
hr {
    border-bottom: 0 !important;
    height: 1px;
    background: linear-gradient(to right, transparent, rgba(212, 175, 55, 0.6), transparent);
    margin: 2em 0;
}

/* dataframe 表格样式覆盖 */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(212,175,55,0.3);
}
th {
    background-color: #1a1814 !important;
    color: #d4af37 !important;
    border-bottom: 1px solid #d4af37 !important;
}
td {
    background-color: #0a0908 !important;
    color: #eaddc5 !important;
    border-bottom: 1px solid rgba(212,175,55,0.1) !important;
}

/* 滚动条赛博化 */
::-webkit-scrollbar {
    width: 4px;
    height: 4px;
}
::-webkit-scrollbar-track {
    background: #050505;
}
::-webkit-scrollbar-thumb {
    background: rgba(212, 175, 55, 0.5);
    border-radius: 2px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(212, 175, 55, 0.9);
    box-shadow: 0 0 10px #d4af37;
}

/* 移动端适配 */
@media (max-width: 768px) {
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }
    h1 { font-size: 1.8rem !important; margin-bottom: 15px; }
    h2 { font-size: 1.4rem !important; }
    button[kind="primary"] {
        padding: 12px !important;
        font-size: 16px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# 初始化数据库
init_db()

# ============ Session State 初始化 ============
if "analysis_running" not in st.session_state:
    st.session_state.analysis_running = False
if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False
if "latest_result" not in st.session_state:
    st.session_state.latest_result = None
if "tool_logs" not in st.session_state:
    st.session_state.tool_logs = []
if "thinking_logs" not in st.session_state:
    st.session_state.thinking_logs = []


# ============ 侧边栏导航 ============
st.sidebar.title("📊 A股 AI 分析顾问")
st.sidebar.divider()

page = st.sidebar.radio(
    "导航",
    [
        "📊 分析报告",
        "📜 历史记录",
        "🎯 准确率追踪",
        "⚙️ 设置",
    ],
    label_visibility="collapsed",
)


import os

# ============ 📊 分析报告页 ============
if page == "📊 分析报告":
    st.title("A股 AI 分析顾问")
    # 注入高质量 AI Banner
    banner_img = r"C:\Users\83158\.gemini\antigravity\brain\2dc9410d-99c3-4eb5-9f3a-e802a57713e5\premium_ai_advisor_banner_1774433423046.png"
    if os.path.exists(banner_img):
        st.image(banner_img, use_container_width=True)

    # 配置校验
    config_errors = validate_config()
    if config_errors:
        for err in config_errors:
            st.error(f"⚠️ {err}")

    # 运行分析按钮区
    col1, col2 = st.columns([1, 1])
    with col1:
        run_button = st.button(
            "🚀 运行分析",
            type="primary",
            disabled=st.session_state.analysis_running or bool(config_errors),
            use_container_width=True,
        )
    with col2:
        stop_button = st.button(
            "🛑 停止分析",
            disabled=not st.session_state.analysis_running,
            use_container_width=True,
        )

    if stop_button:
        st.session_state.stop_requested = True
        st.warning("⏳ 正在停止分析...")

    if run_button and not st.session_state.analysis_running:
        st.session_state.analysis_running = True
        st.session_state.stop_requested = False
        st.session_state.tool_logs = []
        st.session_state.thinking_logs = []

        progress_container = st.container()
        with progress_container:
            status_text = st.empty()
            tool_log_area = st.empty()

            status_text.info("🤖 AI Agent 正在收集数据并分析中...")

            # 回调函数
            tool_logs = []
            thinking_logs = []

            def on_tool_call(name, inputs):
                tool_logs.append(f"🔧 调用工具: {name}")

            def on_thinking(text):
                thinking_logs.append(text[:200])

            def stop_check():
                return st.session_state.stop_requested

            # 执行分析
            try:
                result = run_analysis(
                    on_tool_call=on_tool_call,
                    on_thinking=on_thinking,
                    stop_flag=stop_check,
                )
                st.session_state.latest_result = result
                st.session_state.tool_logs = tool_logs
                st.session_state.thinking_logs = thinking_logs
            except Exception as e:
                st.session_state.latest_result = {
                    "success": False,
                    "error": str(e),
                    "report": None,
                }
            finally:
                st.session_state.analysis_running = False
                st.rerun()

    # 展示最新结果
    result = st.session_state.latest_result
    if result:
        if result.get("success"):
            report = result["report"]
            st.success(f"✅ 分析完成！报告 ID: {result.get('report_id')}")

            # 市场概况
            if report.get("market_summary"):
                st.subheader("🌐 市场概况")
                st.info(report["market_summary"])

            # 推荐列表
            if report.get("recommendations"):
                st.subheader("💡 推荐标的")
                for rec in report["recommendations"]:
                    action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(
                        rec.get("action"), "⚪"
                    )
                    confidence_badge = {
                        "HIGH": "🔥 高",
                        "MEDIUM": "⚡ 中",
                        "LOW": "💤 低",
                    }.get(rec.get("confidence"), "")

                    with st.expander(
                        f"{action_emoji} {rec.get('name', '')} ({rec.get('symbol', '')}) — {rec.get('action', '')} | 置信度: {confidence_badge}",
                        expanded=True,
                    ):
                        st.write(f"**推荐理由**: {rec.get('reason', '')}")

                        if rec.get("analysis_process"):
                            st.write("**分析过程:**")
                            for step in rec["analysis_process"]:
                                st.write(f"  {step}")

                        if rec.get("data_sources"):
                            st.write("**数据来源:**")
                            for src in rec["data_sources"]:
                                st.write(f"  📎 {src}")

                        if rec.get("risk_note"):
                            st.warning(f"⚠️ 风险提示: {rec['risk_note']}")

            # 自选股更新
            if report.get("watchlist_updates"):
                st.subheader("👀 自选股观察")
                for item in report["watchlist_updates"]:
                    st.write(
                        f"🟡 **{item.get('name', '')}** ({item.get('symbol', '')}): {item.get('reason', '')}"
                    )

            # 工具调用日志
            if result.get("tool_calls_log"):
                with st.expander("🔧 Agent 工具调用日志", expanded=False):
                    for log in result["tool_calls_log"]:
                        st.code(
                            f"[轮次 {log['round']}] {log['tool']}({json.dumps(log['input'], ensure_ascii=False)[:100]})",
                            language=None,
                        )
        else:
            st.error(f"❌ 分析失败: {result.get('error', '未知错误')}")
            if result.get("raw_output"):
                with st.expander("原始输出"):
                    st.text(result["raw_output"])

    # 工具调用实时日志
    if st.session_state.tool_logs:
        with st.expander("📡 本次工具调用记录", expanded=False):
            for log in st.session_state.tool_logs:
                st.text(log)


# ============ 📜 历史记录页 ============
elif page == "📜 历史记录":
    st.title("📜 历史分析记录")

    reports = get_history_reports(limit=50)
    if not reports:
        st.info("暂无历史记录，请先运行一次分析。")
    else:
        for report_row in reports:
            report_id = report_row["id"]
            timestamp = report_row["timestamp"]
            summary = report_row.get("market_summary", "")[:100]

            with st.expander(f"📋 报告 #{report_id} — {timestamp}"):
                st.write(f"**市场概况**: {report_row.get('market_summary', '')}")

                # 解析完整报告
                try:
                    full_report = json.loads(report_row.get("report_json", "{}"))
                    for rec in full_report.get("recommendations", []):
                        action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(
                            rec.get("action"), "⚪"
                        )
                        st.write(
                            f"{action_emoji} **{rec.get('name', '')}** ({rec.get('symbol', '')}) "
                            f"— {rec.get('action', '')} | {rec.get('reason', '')[:80]}"
                        )
                except json.JSONDecodeError:
                    st.error("报告数据解析失败")


# ============ 🎯 准确率追踪页 ============
elif page == "🎯 准确率追踪":
    st.title("🎯 推荐准确率追踪")

    stats = get_accuracy_stats()

    # 概览面板
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总推荐数", stats["total"])
    col2.metric("命中", stats["wins"], delta=None)
    col3.metric("未中", stats["losses"], delta=None)
    col4.metric(
        "胜率",
        f"{stats['win_rate']}%",
        delta=f"{stats['pending']} 待标记",
    )

    st.divider()

    # 推荐记录列表
    records = get_accuracy_records()
    if records:
        st.subheader("标记推荐结果")
        for record in records:
            if record["actual_result"] == "PENDING":
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(
                        f"**{record.get('name', '')}** ({record.get('symbol', '')}) "
                        f"— {record.get('action', '')} | {record.get('confidence', '')}"
                    )
                with col2:
                    if st.button("✅ 命中", key=f"win_{record['id']}"):
                        update_accuracy(record["id"], "WIN")
                        st.rerun()
                with col3:
                    if st.button("❌ 未中", key=f"lose_{record['id']}"):
                        update_accuracy(record["id"], "LOSE")
                        st.rerun()
            else:
                result_emoji = "✅" if record["actual_result"] == "WIN" else "❌"
                st.write(
                    f"{result_emoji} **{record.get('name', '')}** ({record.get('symbol', '')}) "
                    f"— {record.get('action', '')} | 标记于 {record.get('marked_at', '')}"
                )
    else:
        st.info("暂无推荐记录。")


# ============ ⚙️ 设置页 ============
elif page == "⚙️ 设置":
    st.title("⚙️ 系统设置")

    st.subheader("📋 当前关注股票白名单")
    if WATCHLIST:
        watchlist_df = pd.DataFrame(
            [{"代码": code, "名称": name} for code, name in WATCHLIST.items()]
        )
        st.dataframe(watchlist_df, use_container_width=True, hide_index=True)
    else:
        st.warning("白名单为空！")

    st.info(
        "💡 **修改白名单**: 编辑 `config/settings.py` 文件中的 `WATCHLIST` 字典，"
        "添加或移除股票代码和名称。"
    )

    st.divider()
    st.subheader("🔑 环境配置状态")
    config_errors = validate_config()
    if config_errors:
        for err in config_errors:
            st.error(f"⚠️ {err}")
    else:
        st.success("✅ 所有配置正常")

    st.divider()
    st.subheader("ℹ️ 系统信息")
    from config.settings import CLAUDE_MODEL, MAX_TOKENS
    st.json({
        "Claude 模型": CLAUDE_MODEL,
        "最大 Token": MAX_TOKENS,
        "关注股票数": len(WATCHLIST),
        "数据库路径": str(st.session_state.get("db_path", "storage/reports.db")),
    })

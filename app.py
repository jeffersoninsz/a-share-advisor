"""
A 股 AI 量化分析顾问 — Streamlit Dashboard
系统唯一的前端入口。

启动方式: streamlit run app.py
"""

from config.utf8_setup import ensure_utf8_output
ensure_utf8_output()

import os
import sys
from pathlib import Path

# --- HOTFIX FOR STREAMLIT CLOUD ---
# Streamlit Cloud has read-only site-packages which crashes efinance.
# We temporarily ignore mkdir PermissionErrors during import and then remap its cache path.
_original_mkdir = Path.mkdir

def _safe_mkdir(self, mode=0o777, parents=False, exist_ok=False):
    try:
        _original_mkdir(self, mode=mode, parents=parents, exist_ok=exist_ok)
    except PermissionError:
        pass

Path.mkdir = _safe_mkdir

try:
    import efinance
    import efinance.config
    import efinance.shared
    
    _temp_dir = Path(__file__).parent / "storage" / "efinance_data"
    _original_mkdir(_temp_dir, parents=True, exist_ok=True)
    
    efinance.config.DATA_DIR = _temp_dir
    efinance.config.SEARCH_RESULT_CACHE_PATH = str(_temp_dir / "search-cache.json")
    efinance.shared.SEARCH_RESULT_CACHE_PATH = str(_temp_dir / "search-cache.json")
except Exception:
    pass
finally:
    Path.mkdir = _original_mkdir
# ----------------------------------

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
    page_title="王镇超级AI股票助手VER1",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ 动态背景加载 ============
import base64
from pathlib import Path

@st.cache_data
def get_base64_of_bin_file(bin_file):
    try:
        # Use absolute path relative to this script to ensure reliability across CWDs
        abs_path = Path(__file__).parent / bin_file
        if not abs_path.exists():
            return ""
        with open(abs_path, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

# 同时加载背景图和可能的 Premium 备选
bg_base64 = get_base64_of_bin_file('assets/bg_premium.png')
image_type = "bg_premium"
if not bg_base64:
    bg_base64 = get_base64_of_bin_file('assets/bg_new.png')
    image_type = "bg_new"

# ============ 自定义 CSS (黑金赛博) ============
st.markdown(f"""
<style>
/* 古典衬线与神秘感字体 */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Noto+Serif+SC:wght@300;400;700&display=swap');

/* 全局字体 */
html, body, [class*="st-"] {{
    font-family: 'Noto Serif SC', 'Cinzel', serif;
}}

/* 坚决保护所有 Streamlit 图标字体，防止显示为原始文本 (如 keyboard_arrow_right) */
.material-icons, .material-symbols-rounded, .stIcon, [data-testid="stIconMaterial"] {{
    font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
}}

/* ============ 动态背景 ============ */
.stApp {{
    background-image: 
        radial-gradient(circle at 50% 50%, rgba(10, 8, 5, 0.75) 0%, rgba(5, 5, 5, 0.98) 100%),
        url("data:image/png;base64,{bg_base64}") !important;
    background-size: cover !important;
    background-position: center !important;
    background-attachment: fixed !important;
    background-repeat: no-repeat !important;
    background-color: transparent !important;
}}

/* ============ 主内容玻璃拟态面板 ============ */
/* 不强制覆盖 padding，尊重 Streamlit 的移动端自适应 */
.block-container {{
    background: rgba(12, 10, 8, 0.8) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(212, 175, 55, 0.15) !important;
    border-radius: 12px !important;
    margin-top: 2rem !important;
    margin-bottom: 2rem !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8);
}}

/* 侧边栏及顶栏透明化处理 */
header[data-testid="stHeader"] {{
    background: transparent !important;
}}

[data-testid="stSidebar"] {{
    background-color: rgba(8, 7, 7, 0.95) !important;
    backdrop-filter: blur(15px);
    border-right: 1px solid rgba(212, 175, 55, 0.3) !important;
}}

/* 仅隐藏 Deploy 和右上角菜单，绝对不隐藏整个 Header 或 Toolbar 影响侧边栏展开按钮 */
.stDeployButton, [data-testid="stAppDeployButton"], #MainMenu, [data-testid="stHeaderActionElements"] {{
    display: none !important;
}}

/* 发光标题特效 */
h1, h2, h3 {{
    text-shadow: 0 0 10px rgba(212, 175, 55, 0.4);
    font-weight: 600 !important;
    color: #f7e096 !important;
}}
h1 {{
    text-align: center;
    border-bottom: 2px solid transparent;
    border-image: linear-gradient(90deg, transparent, #d4af37, transparent) 1;
    padding-bottom: 10px;
    margin-bottom: 20px;
}}

/* 容器与卡片边界：发光特效与毛玻璃 */
div[data-testid="metric-container"], 
div[data-testid="stExpander"], 
.stAlert {{
    background: rgba(18, 15, 12, 0.85) !important;
    border: 1px solid rgba(212, 175, 55, 0.25) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6) !important;
    color: #eaddc5 !important;
    transition: all 0.3s ease;
}}

div[data-testid="stExpander"]:hover, div[data-testid="metric-container"]:hover {{
    border-color: rgba(212, 175, 55, 0.6) !important;
    transform: translateY(-2px);
}}

/* 指标卡片文字 */
div[data-testid="metric-container"] label {{
    color: #c4b59d !important;
}}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
    color: #f7e096 !important;
    text-shadow: 0 0 10px rgba(212, 175, 55, 0.6);
}}

/* 按钮样式 */
button[kind="primary"] {{
    background: linear-gradient(135deg, #262116, #12100c) !important;
    border: 1px solid #d4af37 !important;
    color: #d4af37 !important;
    transition: all 0.3s ease;
    font-weight: 600;
}}
button[kind="primary"]:hover {{
    background: linear-gradient(135deg, #d4af37, #b08d28) !important;
    color: #000 !important;
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.5) !important;
    border-color: #fff !important;
}}

button[kind="secondary"] {{
    background: rgba(20, 18, 15, 0.6) !important;
    border: 1px solid rgba(212, 175, 55, 0.3) !important;
    color: #d4af37 !important;
}}
button[kind="secondary"]:hover {{
    background: rgba(212, 175, 55, 0.15) !important;
    border-color: #e5c158 !important;
    color: #fff !important;
}}

/* 分割线鎏金效果 */
hr {{
    border-bottom: 0 !important;
    height: 1px;
    background: linear-gradient(to right, transparent, rgba(212, 175, 55, 0.8), transparent) !important;
    margin: 2em 0;
}}

/* 隐藏 Footer */
footer {{visibility: hidden;}}
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
st.sidebar.title("📊 王镇超级AI股票助手VER1")
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
    st.title("王镇超级AI股票助手VER1")
    # 保持界面简洁，移除顶部静态大图（改为仅使用全屏背景）


    # 配置校验
    config_errors = validate_config()
    if config_errors:
        for err in config_errors:
            st.error(f"⚠️ {err}")

    # -------- 📌 控制面板区 (始终可见) --------
    st.subheader("⚙️ 分析控制台")

    # 加载最新的 WATCHLIST（动态读取，不缓存 import 时的值）
    from config.settings import WATCHLIST_FILE, DEFAULT_WATCHLIST
    import json as _json
    def _load_watchlist():
        try:
            if WATCHLIST_FILE.exists():
                with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                    return _json.load(f)
        except Exception:
            pass
        return DEFAULT_WATCHLIST.copy()

    def _save_watchlist(wl):
        try:
            WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
                _json.dump(wl, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    current_watchlist = _load_watchlist()
    all_stock_options = [f"{code} - {name}" for code, name in current_watchlist.items()]

    # --- 标的选择 ---
    if "selected_stocks" not in st.session_state:
        st.session_state.selected_stocks = all_stock_options

    # 同步：如果 watchlist 变化导致旧选项失效，自动清理
    valid_selected = [s for s in st.session_state.selected_stocks if s in all_stock_options]

    selected = st.multiselect(
        "🎯 选择本次要分析的股票（可多选，留空则分析全部）",
        options=all_stock_options,
        default=valid_selected,
        help="从自选股白名单中选择 AI 重点分析的标的。留空 = 分析全部。",
    )
    st.session_state.selected_stocks = selected

    # --- 快捷操作按钮行 ---
    qc1, qc2, qc3 = st.columns(3)
    with qc1:
        if st.button("✅ 全选", key="select_all_stocks", use_container_width=True):
            st.session_state.selected_stocks = all_stock_options
            st.rerun()
    with qc2:
        if st.button("🚫 全不选", key="deselect_all_stocks", use_container_width=True):
            st.session_state.selected_stocks = []
            st.rerun()
    with qc3:
        if st.button("🔄 恢复默认池", key="reset_watchlist_btn", use_container_width=True):
            _save_watchlist(DEFAULT_WATCHLIST)
            st.session_state.selected_stocks = [f"{c} - {n}" for c, n in DEFAULT_WATCHLIST.items()]
            st.rerun()

    # --- 增删标的 (折叠面板) ---
    with st.expander("➕ 增删管理自选股", expanded=False):
        st.caption("在此添加新股票或删除已有股票，保存后全局生效。")

        # 添加新股票
        add_col1, add_col2, add_col3 = st.columns([2, 3, 1])
        with add_col1:
            new_code = st.text_input("股票代码", placeholder="如 601398", key="new_stock_code")
        with add_col2:
            new_name = st.text_input("股票名称", placeholder="如 工商银行", key="new_stock_name")
        with add_col3:
            st.write("")  # 占位对齐
            st.write("")
            add_btn = st.button("➕ 添加", key="add_stock_btn", use_container_width=True)

        if add_btn:
            code = new_code.strip()
            name = new_name.strip()
            if not code or not name:
                st.error("⚠️ 股票代码和名称不能为空")
            elif code in current_watchlist:
                st.warning(f"⚠️ 股票 {code} 已存在于白名单中")
            else:
                current_watchlist[code] = name
                _save_watchlist(current_watchlist)
                st.session_state.selected_stocks = [f"{c} - {n}" for c, n in current_watchlist.items()]
                st.success(f"✅ 已添加 {name} ({code})")
                st.rerun()

        # 删除现有股票
        if current_watchlist:
            st.divider()
            st.caption("🗑️ 点击右侧按钮删除对应股票：")
            for code, name in list(current_watchlist.items()):
                del_col1, del_col2, _ = st.columns([3, 1, 6])
                with del_col1:
                    st.markdown(f"**{code}** — {name}")
                with del_col2:
                    if st.button("❌", key=f"del_{code}", help=f"删除 {name}"):
                        del current_watchlist[code]
                        _save_watchlist(current_watchlist)
                        # 同步清理选择状态
                        st.session_state.selected_stocks = [
                            s for s in st.session_state.selected_stocks if not s.startswith(code)
                        ]
                        st.success(f"已删除 {name} ({code})")
                        st.rerun()

    st.divider()

    # 运行分析按钮区 (始终固定在此位置)
    _, col1, col2, col3, _ = st.columns([1, 2, 2, 2, 1])
    with col1:
        run_button = st.button(
            "🚀 运行分析",
            type="primary",
            disabled=st.session_state.analysis_running or bool(config_errors),
            use_container_width=True,
            key="run_analysis_btn",
        )
    with col2:
        stop_button = st.button(
            "🛑 停止分析",
            disabled=not st.session_state.analysis_running,
            use_container_width=True,
            key="stop_analysis_btn",
        )
    with col3:
        clear_button = st.button(
            "🗑️ 清空结果",
            disabled=st.session_state.analysis_running,
            use_container_width=True,
            key="clear_results_btn",
        )

    if clear_button:
        st.session_state.latest_result = None
        st.session_state.tool_logs = []
        st.session_state.thinking_logs = []
        st.rerun()

    if stop_button:
        st.session_state.stop_requested = True
        st.warning("⏳ 正在停止分析...")

    if run_button and not st.session_state.analysis_running:
        st.session_state.analysis_running = True
        st.session_state.stop_requested = False
        st.session_state.latest_result = None
        st.session_state.tool_logs = []
        st.session_state.thinking_logs = []

        progress_container = st.container()
        with progress_container:
            status_text = st.empty()

            # 显示本次分析范围
            if selected:
                stock_names = [s.split(" - ")[1] for s in selected]
                status_text.info(f"🤖 AI Agent 正在分析 **{', '.join(stock_names)}** ...")
            else:
                status_text.info("🤖 AI Agent 正在分析全部自选股...")

            # 回调函数
            tool_logs = []
            thinking_logs = []

            def on_tool_call(name, inputs):
                tool_logs.append({"tool": name, "input": inputs})

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

    # -------- 📊 分析结果展示区 --------
    st.divider()
    result = st.session_state.latest_result
    if result:
        if result.get("success"):
            report = result["report"]
            st.success(f"✅ 分析完成！报告 ID: {result.get('report_id')}")

            # ---- 📡 数据源与工具调用链 (显著展示) ----
            tool_log_data = result.get("tool_calls_log", [])
            realtime_logs = st.session_state.tool_logs
            if tool_log_data or realtime_logs:
                st.subheader("📡 本次分析数据源")
                # 汇总所有调用过的工具
                tool_summary = {}
                for log_entry in tool_log_data:
                    t_name = log_entry.get("tool", "")
                    if t_name not in tool_summary:
                        tool_summary[t_name] = 0
                    tool_summary[t_name] += 1

                # 工具名中文映射
                tool_cn_map = {
                    "get_stock_list": "📋 自选股白名单",
                    "get_realtime_quotes": "📈 实时行情报价",
                    "get_kline_data": "📊 K线历史数据",
                    "get_kline_summary": "📉 均线技术摘要",
                    "get_news_feed": "📰 财联社快讯",
                    "get_macro_data": "🏛️ 宏观经济指标",
                    "get_sector_flow": "💰 板块资金流向",
                    "get_north_flow": "🌏 北向资金动向",
                    "get_history_reports": "📜 历史报告回溯",
                }

                if tool_summary:
                    source_cols = st.columns(min(len(tool_summary), 4))
                    for idx, (tool_name, count) in enumerate(tool_summary.items()):
                        cn_name = tool_cn_map.get(tool_name, tool_name)
                        with source_cols[idx % len(source_cols)]:
                            st.metric(cn_name, f"{count} 次调用")

                # 详细工具调用日志
                with st.expander("🔧 Agent 完整工具调用链", expanded=False):
                    for log_entry in tool_log_data:
                        round_num = log_entry.get("round", "?")
                        t_name = log_entry.get("tool", "")
                        t_input = log_entry.get("input", {})
                        t_preview = log_entry.get("output_preview", "")[:200]
                        cn_name = tool_cn_map.get(t_name, t_name)
                        st.markdown(f"**[轮次 {round_num}]** {cn_name}")
                        st.code(
                            f"参数: {json.dumps(t_input, ensure_ascii=False)[:150]}\n返回: {t_preview}",
                            language=None,
                        )

            st.divider()

            # ---- 🌐 市场概况 ----
            if report.get("market_summary"):
                st.subheader("🌐 市场概况")
                st.info(report["market_summary"])

            # ---- 💡 推荐列表 ----
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
                    action_cn = {"BUY": "买入", "SELL": "卖出", "HOLD": "持有"}.get(rec.get("action", ""), rec.get("action", ""))

                    with st.expander(
                        f"{action_emoji} {rec.get('name', '')} ({rec.get('symbol', '')}) — {action_cn} | 置信度: {confidence_badge}",
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

            # ---- 👀 自选股 ----
            if report.get("watchlist_updates"):
                st.subheader("👀 自选股观察")
                for item in report["watchlist_updates"]:
                    st.write(
                        f"🟡 **{item.get('name', '')}** ({item.get('symbol', '')}): {item.get('reason', '')}"
                    )

        else:
            st.error(f"❌ 分析失败: {result.get('error', '未知错误')}")
            if result.get("raw_output"):
                with st.expander("原始输出"):
                    st.text(result["raw_output"])
    elif not st.session_state.analysis_running:
        st.info("👆 点击上方 **🚀 运行分析** 按钮开始 AI 智能分析。您可以先在上方选择要分析的股票标的。")


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
                        action_cn = {"BUY": "买入", "SELL": "卖出", "HOLD": "持有"}.get(rec.get("action", ""), rec.get("action", ""))
                        st.write(
                            f"{action_emoji} **{rec.get('name', '')}** ({rec.get('symbol', '')}) "
                            f"— {action_cn} | {rec.get('reason', '')[:80]}"
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
                    action_cn = {"BUY": "买入", "SELL": "卖出", "HOLD": "持有"}.get(record.get("action", ""), record.get("action", ""))
                    confidence_cn = {"HIGH": "高", "MEDIUM": "中", "LOW": "低"}.get(record.get("confidence", ""), record.get("confidence", ""))
                    st.write(
                        f"**{record.get('name', '')}** ({record.get('symbol', '')}) "
                        f"— {action_cn} | {confidence_cn}"
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
                action_cn = {"BUY": "买入", "SELL": "卖出", "HOLD": "持有"}.get(record.get("action", ""), record.get("action", ""))
                st.write(
                    f"{result_emoji} **{record.get('name', '')}** ({record.get('symbol', '')}) "
                    f"— {action_cn} | 标记于 {record.get('marked_at', '')}"
                )
    else:
        st.info("暂无推荐记录。")


# ============ ⚙️ 设置页 ============
elif page == "⚙️ 设置":
    st.title("⚙️ 系统设置 (热配置中心)")

    st.subheader("🔑 核心大模型 API 配置")
    st.markdown("在此动态更新您的 OpenRouter / Anthropic 秘钥，支持热加载（无需重启）。")
    
    env_path = ".env"
    current_key = ""
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY=") or line.startswith("ANTHROPIC_API_KEY="):
                    current_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if current_key:
                        break
                        
    new_key = st.text_input("API Key (OpenRouter/Anthropic)", value=current_key, type="password", help="输入 sk-or-v1-... 或 sk-ant-... 格式的秘钥")
    
    if st.button("💾 保存配置并注入系统底层环境", type="primary"):
        env_lines = []
        key_found_openrouter = False
        key_found_anthro = False
        baseurl_found = False
        
        is_openrouter = new_key.startswith("sk-or-")
        new_base_url = "https://openrouter.ai/api/v1" if is_openrouter else ""
        
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                env_lines = f.readlines()
        
        with open(env_path, "w", encoding="utf-8") as f:
            for line in env_lines:
                if line.startswith("OPENROUTER_API_KEY="):
                    f.write(f'OPENROUTER_API_KEY="{new_key}"\n')
                    key_found_openrouter = True
                elif line.startswith("ANTHROPIC_API_KEY="):
                    f.write(f'ANTHROPIC_API_KEY="{new_key}"\n')
                    key_found_anthro = True
                elif line.startswith("ANTHROPIC_BASE_URL="):
                    f.write(f'ANTHROPIC_BASE_URL="{new_base_url}"\n')
                    baseurl_found = True
                else:
                    f.write(line)
            if not key_found_openrouter:
                f.write(f'OPENROUTER_API_KEY="{new_key}"\n')
            if not key_found_anthro:
                f.write(f'ANTHROPIC_API_KEY="{new_key}"\n')
            if not baseurl_found:
                f.write(f'ANTHROPIC_BASE_URL="{new_base_url}"\n')
                
        # 强制推入热内存
        os.environ["OPENROUTER_API_KEY"] = new_key
        os.environ["ANTHROPIC_API_KEY"] = new_key
        if new_base_url:
            os.environ["ANTHROPIC_BASE_URL"] = new_base_url
        st.success("✅ API 秘钥已成功落盘至 `.env` 文件并挂载全局内存，Base URL 已安全路由重定向。可返回测试。")

    st.divider()

    st.subheader("📋 动态标的池配置 (白名单)")
    st.markdown("在此您可以直接**增删改**重点跟踪的 A 股白名单池，双击单元格即可输入。支持底部行 `+` 号动态新增。保存后全网自动落盘并即时生效。")
    
    from config.settings import WATCHLIST, WATCHLIST_FILE
    import json
    
    current_watchlist = []
    for code, name in WATCHLIST.items():
        current_watchlist.append({"股票代码": code, "公司名称": name})
        
    watchlist_df = pd.DataFrame(current_watchlist)
    
    # 动态可编辑数据表
    edited_df = st.data_editor(
        watchlist_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "股票代码": st.column_config.TextColumn("股票代码 (如 600519)", required=True),
            "公司名称": st.column_config.TextColumn("公司标的名称", required=True)
        }
    )
    
    if st.button("💾 保存储存该股票池矩阵", type="primary", key="save_watchlist"):
        new_watchlist = {}
        for _, row in edited_df.iterrows():
            code = str(row.get("股票代码", "")).strip()
            name = str(row.get("公司名称", "")).strip()
            if code and name and code != "nan":
                new_watchlist[code] = name
                
        WATCHLIST.clear()
        WATCHLIST.update(new_watchlist)
        
        try:
            with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
                json.dump(WATCHLIST, f, ensure_ascii=False, indent=4)
            st.success(f"✅ 白名单热重制完毕！当前挂载观测池包含 {len(WATCHLIST)} 支标的。")
            st.toast("✅ 白名单实时热更新完毕！")
        except Exception as e:
            st.error(f"❌ 写入配置持久化失败: {str(e)}")

    st.divider()
    st.subheader("ℹ️ 系统底层状态")
    config_errors = validate_config()
    if config_errors:
        for err in config_errors:
            st.error(f"⚠️ {err}")
    else:
        st.success("✅ 全局变量和数据库路径监听正常")

    from config.settings import CLAUDE_MODEL, MAX_TOKENS
    st.json({
        "Claude 模型": CLAUDE_MODEL,
        "最大 Token": MAX_TOKENS,
        "关注股票数": len(WATCHLIST),
        "数据库路径": str(st.session_state.get("db_path", "storage/reports.db")),
    })

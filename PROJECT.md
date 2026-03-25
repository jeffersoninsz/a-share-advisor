# PROJECT.md — A 股 AI 量化分析顾问（SSOT 总纲）

> **本文件是项目唯一的 Single Source of Truth（SSOT）**。任何 AI 助手开始新会话时，必须首先读取本文件获取完整的项目上下文。

---

## 📌 项目概述

| 项目 | 说明 |
|---|---|
| **名称** | A 股 AI 量化分析顾问 |
| **定位** | AI 驱动的 A 股分析顾问系统（仅推荐，不执行交易） |
| **LLM** | Anthropic Claude（Tool Use API） |
| **数据源** | AKShare（财联社/宏观） + efinance（东财 K 线/行情） |
| **前端** | Streamlit Dashboard |
| **数据库** | SQLite（本地轻量） |
| **部署** | 当前本地个人使用，未来可部署 Vercel（≤10 人） |
| **触发方式** | 手动触发（Dashboard 按钮），非自动轮询 |
| **风控级别** | 基础级（risk_note + 白名单 + 隔离会话） |

---

## 🧠 核心设计决策

1. **只推荐不交易**: 系统仅输出分析报告和推荐，最终买卖由用户自行决策
2. **Claude Tool Use 自定义循环**: 不使用 LangGraph/AutoGen 等框架，代码完全透明可控
3. **隔离会话**: 每次分析创建全新 Claude 对话，不复用历史会话，防止脏数据
4. **双数据源互补**: AKShare 擅长新闻/宏观/板块，efinance 擅长 K 线/行情
5. **手动触发优先**: 初期安全可控，后续可升级为定时轮询

---

## 📁 目录结构

```
quantitative_analysis/
├── .env.example                # 环境变量模板
├── .env                        # 实际环境变量（⚠️ 不入 Git）
├── .gitignore
├── .venv/                      # Python 虚拟环境（⚠️ 不入 Git）
├── requirements.txt            # Python 依赖
├── PROJECT.md                  # 本文件（SSOT）
├── app.py                      # Streamlit 入口
│
├── config/
│   ├── __init__.py
│   ├── settings.py             # 全局配置：股票白名单、模型参数
│   └── utf8_setup.py           # UTF-8 输出安全工具
│
├── data/
│   ├── __init__.py
│   ├── fetcher_akshare.py      # AKShare 采集（财联社/宏观/板块/北向资金）
│   ├── fetcher_efinance.py     # efinance 采集（K线/实时报价）
│   └── aggregator.py           # 数据聚合与格式化
│
├── agent/
│   ├── __init__.py
│   ├── brain.py                # AI Agent 核心：Claude Tool Use 循环（最大15轮）
│   ├── tools.py                # 9 个 Agent 工具声明 + dispatch 分发
│   ├── prompts.py              # System Prompt 模板（分析师角色 + 输出 JSON Schema）
│   └── schemas.py              # I/O Schema（复用 Pydantic 模型）
│
├── storage/
│   ├── __init__.py
│   ├── database.py             # SQLite CRUD（报告 + 准确率追踪）
│   ├── models.py               # Pydantic 数据模型
│   └── reports.db              # 数据库文件（⚠️ 不入 Git）
│
├── docs/
│   └── 2026-03-25-ai-stock-advisor-design.md
│
└── tests/
    ├── __init__.py
    ├── test_fetchers.py         # 数据采集测试
    ├── test_agent.py            # Agent 逻辑测试（17项）
    └── test_database.py         # 数据库 CRUD 测试
```

---

## 🔧 环境变量

| 变量名 | 说明 | 示例 |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic Claude API 密钥 | `sk-ant-api03-xxxx` |
| `CLAUDE_MODEL` | 使用的 Claude 模型 | `claude-sonnet-4-20250514` |
| `MAX_TOKENS` | 最大输出 token 数 | `4096` |

---

## 📦 核心依赖

```
anthropic        # Claude API SDK
akshare          # A 股数据 / 财联社 / 宏观指标
efinance         # 东方财富 K 线 / 行情
streamlit        # Dashboard 前端
pandas           # 数据处理
python-dotenv    # 环境变量管理
pydantic         # 数据校验（JSON Schema）
pytest           # 测试框架
```

---

## 🗺 实现路线图

| 阶段 | 内容 | 状态 |
|---|---|---|
| **Phase 1** | 需求与架构设计 | ✅ 已完成 |
| **Phase 2** | 核心基建与数据联调 | ✅ 已完成 |
| **Phase 3** | AI Agent 决策引擎 | ✅ 已完成 |
| **Phase 4** | 可视化控制台 | ✅ 已完成 |
| **Phase 5** | 优化升级（技术指标/定时/部署） | ⬜ 待规划 |

---

## 🚀 快速启动

```powershell
# 1. 进入项目目录
cd "c:\Users\83158\Desktop\quantitative analysis"

# 2. 激活虚拟环境
.venv\Scripts\Activate.ps1

# 3. 配置 API Key（首次使用）
copy .env.example .env
# 编辑 .env 填入你的 ANTHROPIC_API_KEY

# 4. 启动 Dashboard
streamlit run app.py

# 运行测试
python -m pytest tests/ -v
```

---

## 📄 文档清单

| 文件 | 路径 | 说明 |
|---|---|---|
| **SSOT 总纲** | `PROJECT.md` | 本文件，任何新会话必须首先读取 |
| **设计文档** | `docs/2026-03-25-ai-stock-advisor-design.md` | 完整系统设计（架构、数据流、输出格式等） |
| **环境模板** | `.env.example` | 环境变量说明 |
| **依赖列表** | `requirements.txt` | Python 依赖 |

---

## ⚠️ AI 助手接力规则

> 如果你是新会话的 AI 助手，请遵守以下规则：
> 1. **必须首先阅读本文件** 获取项目全貌
> 2. **然后阅读 `docs/2026-03-25-ai-stock-advisor-design.md`** 获取详细设计
> 3. **检查实现路线图** 确认当前处于哪个阶段
> 4. **不要重新设计** 已确认的架构决策（见核心设计决策部分）
> 5. **所有变更必须同步更新** 本文件的路线图状态

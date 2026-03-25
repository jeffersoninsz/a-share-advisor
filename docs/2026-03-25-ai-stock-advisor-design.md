# A 股 AI 量化分析顾问 — 系统设计文档

> **文档版本**: v1.2 | **最后更新**: 2026-03-25
> **系统定位**: AI 驱动的 A 股分析顾问系统。仅提供推荐与分析报告，不执行任何交易操作。最终决策由用户自行做出。

---

## 1. 核心需求

### 1.1 系统做什么
- 采集 A 股实时行情、财联社 7x24 快讯、宏观经济数据
- 通过 Claude AI Agent 自主分析多维度数据
- 输出结构化推荐报告（推荐标的、理由、分析流程、数据来源、风险提示）
- 记录历史推荐，追踪准确率

### 1.2 系统不做什么
- ❌ 不自动下单、不执行买卖操作
- ❌ 不涉及加密货币
- ❌ 不涉及 A 股以外的市场

### 1.3 触发方式
- 手动触发：用户在 Dashboard 上点击「运行分析」按钮
- 未来可扩展为定时轮询

### 1.4 部署与使用场景
- **当前阶段**: 本地单人使用，`streamlit run app.py` 启动
- **未来扩展**: 部署到 Vercel 服务器，使用人数不超过 10 人
- **数据存储**: SQLite 本地数据库，未来可迁移至 PostgreSQL

---

## 2. 系统架构

```
┌──────────────────────────────────────────────┐
│              用户 (Streamlit Dashboard)        │
│   点击 [运行分析] → 查看推荐报告 → 自行决策    │
└─────────────────────┬────────────────────────┘
                      │ 触发
                      ▼
┌──────────────────────────────────────────────┐
│          调度器 (Main Orchestrator)            │
│  1. 启动 AI Agent 分析会话（隔离会话）         │
│  2. Agent 通过 Tool Use 自主采集所需数据       │
│  3. Agent 输出结构化推荐报告 JSON              │
│  4. 保存报告到 SQLite                         │
│  5. 推送结果到 Dashboard 展示                  │
└─────────────────────┬────────────────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
  ┌────────────┐ ┌──────────┐ ┌──────────────┐
  │ Data Tools │ │ AI Agent │ │  Report DB   │
  │ (数据工具)  │ │ (Claude) │ │  (SQLite)    │
  │            │ │          │ │              │
  │• AKShare   │ │• Tool Use│ │• 推荐历史    │
  │• efinance  │ │• 分析推理 │ │• 准确率追踪  │
  │            │ │• 结构输出 │ │• 分析日志    │
  └────────────┘ └──────────┘ └──────────────┘
```

### 2.1 核心角色

| 角色 | 职责 | 技术实现 |
|---|---|---|
| **调度器** | 接收用户触发，启动分析会话，保存结果 | Python 主函数 |
| **AI Agent** | 自主调用工具收集数据，推理分析，输出推荐 | Claude Tool Use API |
| **数据工具** | 提供 A 股行情、新闻、宏观数据 | AKShare + efinance |
| **报告数据库** | 持久化推荐记录与分析日志 | SQLite |
| **Dashboard** | 展示推荐报告、历史记录、准确率 | Streamlit |

### 2.2 Agent Tool Use 工作流

```
用户点击 [运行分析]
    │
    ▼
Agent 收到 System Prompt + 当前时间
    │
    ├─→ Agent 调用 tool: get_stock_list()        → 获取关注的股票列表
    ├─→ Agent 调用 tool: get_realtime_quotes()   → 获取实时行情
    ├─→ Agent 调用 tool: get_kline_data()        → 获取 K 线数据
    ├─→ Agent 调用 tool: get_news_feed()         → 获取财联社快讯
    ├─→ Agent 调用 tool: get_macro_data()        → 获取宏观指标
    ├─→ Agent 调用 tool: get_sector_flow()       → 获取板块资金流向
    ├─→ Agent 调用 tool: get_history_reports()   → 获取历史推荐记录
    │
    ▼
Agent 综合分析，输出结构化 JSON 报告
    │
    ▼
保存到 SQLite → 展示到 Dashboard
```

> **关键**: Agent 自主决定调用哪些工具、调用多少次，而非预设固定流程。每次分析为独立隔离会话。

### 2.3 隔离会话机制

- 每次点击「运行分析」创建一个全新的 Claude 对话会话
- 不复用上一次的会话历史（防止脏数据污染）
- 上一次推荐结果通过 `get_history_reports()` 工具显式传入（而非隐式残留）

---

## 3. 数据源

| 数据源 | Python 库 | 提供的数据 | 核心函数参考 |
|---|---|---|---|
| **财联社 7x24** | `akshare` | 实时财经快讯、政策动态、市场情绪 | `ak.stock_zh_a_alerts_cls()` |
| **A 股实时行情** | `akshare` / `efinance` | 个股实时报价、涨跌幅、成交量 | `ef.stock.get_realtime_quotes()` |
| **K 线数据** | `efinance` | 日/周 K 线、技术指标基础数据 | `ef.stock.get_quote_history()` |
| **宏观数据** | `akshare` | CPI、PMI、社融、M2、LPR 等 | `ak.macro_china_*()` 系列 |
| **板块数据** | `akshare` | 行业板块涨跌排名、资金流向 | `ak.stock_board_industry_*()` |
| **北向资金** | `akshare` | 沪深港通北向资金净流入 | `ak.stock_hsgt_north_*()` |

> **注意**: 以上函数名为参考，实际实现时需查阅 AKShare/efinance 最新 API 文档确认。

---

## 4. AI Agent 输出格式

每次分析输出一个结构化 JSON 报告：

```json
{
  "timestamp": "2026-03-25T16:00:00+08:00",
  "market_summary": "今日 A 股三大指数集体高开，北向资金净流入 52 亿...",
  "recommendations": [
    {
      "symbol": "600519",
      "name": "贵州茅台",
      "action": "BUY",
      "confidence": "HIGH",
      "reason": "白酒板块资金持续流入，茅台站稳 1800 支撑位...",
      "analysis_process": [
        "1. 查看板块资金流向 → 白酒板块净流入 8.2 亿",
        "2. 查看茅台日 K → 站稳 1800 支撑，MACD 金叉",
        "3. 查看财联社快讯 → 消费升级政策利好",
        "4. 综合研判 → 短期看多，目标位 1880"
      ],
      "data_sources": [
        "efinance 600519 日K线数据",
        "AKShare 白酒板块资金流向",
        "财联社快讯 #39821"
      ],
      "risk_note": "注意：年报季临近，关注业绩预告风险"
    }
  ],
  "watchlist_updates": [
    {
      "symbol": "300750",
      "name": "宁德时代",
      "action": "HOLD",
      "reason": "新能源板块震荡，等待方向选择"
    }
  ]
}
```

### 4.1 关键字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `timestamp` | ISO 8601 字符串 | 分析时间戳 |
| `market_summary` | 字符串 | 市场整体概况 |
| `action` | BUY / SELL / HOLD | 方向建议 |
| `confidence` | HIGH / MEDIUM / LOW | 置信度 |
| `analysis_process` | 字符串数组 | 逐步推理过程（透明可审计） |
| `data_sources` | 字符串数组 | 每条结论的数据来源（可追溯） |
| `risk_note` | 字符串 | 风险提示 |

---

## 5. 技术栈

| 层级 | 技术选型 | 版本 | 说明 |
|---|---|---|---|
| **语言** | Python | 3.11+ | 全栈统一 |
| **LLM** | `anthropic` SDK | latest | Claude Tool Use API |
| **A 股行情** | `akshare` | latest | 财联社快讯、宏观数据、板块数据 |
| **K 线数据** | `efinance` | latest | 东方财富 K 线、实时报价 |
| **数据库** | SQLite | 内置 | 本地轻量，存推荐历史和分析日志 |
| **前端 GUI** | Streamlit | latest | 最轻量的 Python Dashboard |
| **配置管理** | `python-dotenv` | latest | .env 管理 API Key |
| **数据处理** | `pandas` | latest | 行情数据清洗 |

---

## 6. 目录结构

```
quantitative_analysis/          ← 项目根目录
│
├── .env.example                # 环境变量模板（含注释说明）
├── .env                        # 实际环境变量（⚠️ Git忽略）
├── .gitignore                  # Git 忽略规则
├── requirements.txt            # Python 依赖列表
├── PROJECT.md                  # 项目 SSOT 文档（防失忆总纲）
│
├── config/
│   ├── __init__.py
│   └── settings.py             # 全局配置：关注股票白名单、分析参数、模型参数
│
├── data/
│   ├── __init__.py
│   ├── fetcher_akshare.py      # AKShare 数据采集（财联社/宏观/板块/北向资金）
│   ├── fetcher_efinance.py     # efinance 数据采集（K线/实时报价）
│   └── aggregator.py           # 数据聚合器（合并多源数据、格式标准化）
│
├── agent/
│   ├── __init__.py
│   ├── brain.py                # AI Agent 核心：Claude Tool Use 循环引擎
│   ├── tools.py                # Agent 可调用的工具函数定义（映射到 data/ 模块）
│   ├── prompts.py              # System Prompt 模板（含分析规则、输出格式要求）
│   └── schemas.py              # 输入/输出 JSON Schema 定义（Pydantic 模型）
│
├── storage/
│   ├── __init__.py
│   ├── database.py             # SQLite 数据库操作（连接、存储、查询）
│   ├── models.py               # 数据表定义（推荐记录表、分析日志表）
│   └── reports.db              # SQLite 数据库文件（⚠️ Git忽略）
│
├── app.py                      # Streamlit Dashboard 入口（唯一 UI 入口）
│
├── docs/
│   └── 2026-03-25-ai-stock-advisor-design.md  # 本设计文档
│
└── tests/
    ├── __init__.py
    ├── test_fetchers.py        # 数据采集连通性测试
    ├── test_agent.py           # Agent 输出格式与逻辑测试
    └── test_database.py        # 数据库 CRUD 测试
```

---

## 7. Dashboard 功能（Streamlit）

| 页面 | 功能 | 优先级 |
|---|---|---|
| **📊 分析报告** | 展示最新一次 AI 分析的推荐报告，含推理过程和数据来源 | P0 |
| **📈 市场概览** | A 股三大指数、板块热力图、北向资金 | P1 |
| **📜 历史记录** | 所有历史推荐列表，可查看每次的完整分析报告 | P0 |
| **🎯 准确率追踪** | 统计历史推荐的命中率（用户手动标记推荐结果后计算） | P1 |
| **⚙️ 设置** | 配置关注股票白名单、分析参数 | P1 |
| **🛑 停止分析** | 中断正在运行的分析任务 | P0 |

---

## 8. 风控设计（基础级）

- Agent 在推荐中必须包含 `risk_note` 风险提示
- 配置文件中设置关注股票的白名单（只分析白名单内的标的）
- 每次分析为独立隔离会话，不受前次脏数据影响
- 历史推荐记录全量保存，便于复盘审计

---

## 9. 验证计划

### 自动化测试
- `test_fetchers.py`: 验证 AKShare / efinance 数据接口连通性，检查返回数据结构
- `test_agent.py`: 使用 Mock 数据验证 Agent 输出 JSON 格式正确性（Pydantic 校验）
- `test_database.py`: 验证 SQLite 报告存储与查询（CRUD 操作）

### 手动验证
- 运行 `streamlit run app.py`，在浏览器中点击「运行分析」
- 验证 AI 输出的推荐报告结构完整、数据来源可追溯
- 验证历史记录正确保存和展示

### 运行测试命令
```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行单个模块测试
python -m pytest tests/test_fetchers.py -v
python -m pytest tests/test_agent.py -v
python -m pytest tests/test_database.py -v
```

---

## 10. 实现路线图

| 阶段 | 内容 | 交付物 |
|---|---|---|
| **Phase 1** | 需求与架构设计 | 本文档 + PROJECT.md |
| **Phase 2** | 核心基建与数据联调 | `data/` 模块 + `storage/` 模块 + `config/` + 测试 |
| **Phase 3** | AI Agent 决策引擎 | `agent/` 模块 + 测试 |
| **Phase 4** | 可视化控制台 | `app.py` + 集成测试 |

每个阶段完成后，等待用户确认「继续」再进入下一阶段。

---

## 11. 关键设计决策记录 (ADR)

| # | 决策 | 理由 |
|---|---|---|
| ADR-1 | 使用 Claude 而非 GPT-4 | 超长上下文窗口，适合分析大量历史数据 |
| ADR-2 | Claude Tool Use 自定义循环，而非 LangGraph | 代码完全可控、无重量级框架依赖、手动触发场景足够 |
| ADR-3 | 仅推荐不执行交易 | 系统定位为分析顾问，最终决策由用户做出 |
| ADR-4 | AKShare + efinance 双数据源 | AKShare 覆盖新闻/宏观，efinance 擅长 K 线/行情，互补 |
| ADR-5 | SQLite 而非 PostgreSQL | 本地单人使用，零配置即可运行 |
| ADR-6 | Streamlit 而非 Gradio | Streamlit 更适合数据展示型 Dashboard |
| ADR-7 | 手动触发而非自动轮询 | 初期更安全可控，降低误操作风险 |
| ADR-8 | 基础级风控 | 初期 MVP，后续迭代加强 |

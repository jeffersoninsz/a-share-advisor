# A 股 AI 量化分析顾问 — 用户手册

> 版本 1.0 | 更新时间: 2026-03-25

---

## 📖 目录

1. [系统简介](#系统简介)
2. [环境准备](#环境准备)
3. [安装与配置](#安装与配置)
4. [启动系统](#启动系统)
5. [功能说明](#功能说明)
6. [常见问题 FAQ](#常见问题-faq)
7. [自定义配置](#自定义配置)
8. [技术架构](#技术架构)

---

## 系统简介

**A 股 AI 量化分析顾问**是一个基于 Claude AI 的 A 股智能分析系统。它能自动收集实时市场数据、财经快讯和宏观指标，通过 AI 分析生成结构化的股票推荐报告。

### 核心特点

| 特点 | 说明 |
|---|---|
| 🤖 AI 驱动 | 使用 Claude 大模型进行多维度分析 |
| 📊 数据透明 | 每条推荐附带完整分析过程和数据来源 |
| 🔒 仅推荐不交易 | 系统只提供分析建议，不会执行任何交易操作 |
| 📈 多维分析 | 宏观面 + 板块面 + 个股面 + 历史复盘 |
| 🎯 准确率追踪 | 人工标记推荐结果，持续评估系统表现 |

### ⚠️ 免责声明

> 本系统仅供学习研究使用，不构成任何投资建议。股市有风险，投资需谨慎。所有最终交易决策应由用户自行做出。

---

## 环境准备

### 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.10 或更高版本
- **网络**: 需要能访互联网（数据采集和 API 调用）
- **磁盘空间**: 约 500MB（含虚拟环境）

### 所需账号

| 服务 | 说明 | 获取方式 |
|---|---|---|
| Anthropic API Key | Claude AI 模型访问密钥 | https://console.anthropic.com |

---

## 安装与配置

### 第一步：进入项目目录

```powershell
cd "c:\Users\83158\Desktop\quantitative analysis"
```

### 第二步：激活虚拟环境

```powershell
# 激活虚拟环境（每次使用前必须运行）
.venv\Scripts\Activate.ps1
```

激活成功后，命令行前面会出现 `(.venv)` 标志。

> 💡 如果遇到 PowerShell 执行策略报错，请先运行：
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 第三步：配置 API Key

编辑项目根目录的 `.env` 文件：

```ini
# 填入你的 Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-xxxx-your-key-here

# 如果使用代理/中转服务，填入自定义 URL（可选）
ANTHROPIC_BASE_URL=https://your-proxy-url.com

# Claude 模型（通常不需要修改）
CLAUDE_MODEL=claude-sonnet-4-20250514

# 最大输出 token 数
MAX_TOKENS=4096
```

### 第四步：验证安装

```powershell
# 运行测试，确认一切正常
python -m pytest tests/ -v
```

预期输出：`24 passed`（全部通过）。

---

## 启动系统

```powershell
# 1. 激活虚拟环境
.venv\Scripts\Activate.ps1

# 2. 启动 Dashboard
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`，看到分析顾问界面。

如果浏览器未自动打开，手动访问 `http://localhost:8501`。

### 停止系统

在终端中按 `Ctrl + C` 即可停止 Streamlit 服务。

---

## 功能说明

### 📊 页面一：分析报告

这是系统的核心页面。

**使用步骤：**

1. 点击 **「🚀 运行分析」** 按钮
2. AI 会自动调用 9 个工具收集数据（耗时约 1-3 分钟）
3. 分析完成后，页面展示完整报告

**报告内容：**

| 模块 | 说明 |
|---|---|
| 🌐 市场概况 | 当前 A 股整体市况总结 |
| 💡 推荐标的 | 具体股票的 BUY/SELL/HOLD 建议 |
| 👀 自选股观察 | 暂无明确信号但值得关注的标的 |
| 🔧 工具调用日志 | AI 调用了哪些工具、获取了什么数据 |

**每条推荐包含：**

- ✅ 推荐动作（买入/卖出/持有）
- 📊 置信度评级（高/中/低）
- 📝 推荐理由
- 🔍 完整分析过程（可审计）
- 📎 数据来源（可追溯）
- ⚠️ 风险提示

### 📜 页面二：历史记录

查看所有历史分析报告，按时间倒序排列。点击展开可查看详细内容。

### 🎯 页面三：准确率追踪

追踪推荐的实际效果：

1. 系统列出所有历史推荐
2. 等待推荐生效后（如 3-5 天），手动标记：
   - ✅ **命中** — 推荐方向正确
   - ❌ **未中** — 推荐方向错误
3. 系统自动计算胜率统计

### ⚙️ 页面四：设置

查看当前系统配置：

- 关注股票白名单
- API 配置状态
- 模型参数

---

## 常见问题 FAQ

### Q: API Key 从哪获取？

访问 [Anthropic Console](https://console.anthropic.com)，注册账号后在 API Keys 页面创建。

### Q: 分析一次要花多少钱？

每次分析大约消耗 5,000-15,000 tokens（包含工具调用），按 Claude Sonnet 定价约 ¥0.2-0.5 / 次。

### Q: 如何修改关注股票？

编辑 `config/settings.py` 文件中的 `WATCHLIST` 字典：

```python
WATCHLIST = {
    "600519": "贵州茅台",
    "300750": "宁德时代",
    # 添加新股票:
    "601888": "中国中免",
}
```

保存后重启 Streamlit 即可生效。

### Q: 分析报告保存在哪？

保存在 `storage/reports.db`（SQLite 数据库）。该文件在 `.gitignore` 中，不会被 Git 跟踪。

### Q: 如何使用代理/中转 API 服务？

在 `.env` 文件中设置 `ANTHROPIC_BASE_URL`：

```ini
ANTHROPIC_BASE_URL=https://your-proxy.com/claude/aws
```

### Q: 数据采集失败怎么办？

1. 检查网络连接是否正常
2. `akshare` 或 `efinance` 的接口偶尔会更新，运行 `pip install --upgrade akshare efinance` 尝试更新

### Q: 虚拟环境激活失败？

```powershell
# 如果 PowerShell 报执行策略错误
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然后重新激活
.venv\Scripts\Activate.ps1
```

---

## 自定义配置

### 环境变量说明

| 变量 | 默认值 | 说明 |
|---|---|---|
| `ANTHROPIC_API_KEY` | (必填) | Claude API 密钥 |
| `ANTHROPIC_BASE_URL` | (空=官方) | 自定义 API 端点 |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude 模型 |
| `MAX_TOKENS` | `4096` | 最大输出 token 数 |
| `NEWS_FETCH_LIMIT` | `50` | 拉取快讯条数 |
| `HISTORY_REPORT_LIMIT` | `10` | 历史报告查询条数 |

### AI Agent 使用的 9 个工具

| 工具名 | 功能 |
|---|---|
| `get_stock_list` | 获取关注股票白名单 |
| `get_realtime_quotes` | 实时行情报价 |
| `get_kline_data` | K 线历史数据 |
| `get_kline_summary` | K 线技术摘要（MA5/MA20） |
| `get_news_feed` | 财联社 7x24 快讯 |
| `get_macro_data` | 宏观经济指标（CPI/PMI） |
| `get_sector_flow` | 行业板块资金流向 |
| `get_north_flow` | 北向资金（外资）流向 |
| `get_history_reports` | 历史推荐记录 |

---

## 🚀 部署到云服务器

本项目基于 Streamlit，部署方案需要特别注意平台限制：

### ❌ 关于 Vercel 部署 (不推荐)

虽然 Vercel 极其流行，但**它并不适合运行 Streamlit 应用**。原因如下：
1. **网络底层协议**：Streamlit 强依赖于 WebSocket 进行前后端长连接通信，而 Vercel 的 Serverless Functions 不支持长连接 WebSocket。
2. **执行超时限制**：Vercel 免费版 (Hobby) Serverless 函数最大超时时间为 **10秒**（Pro版 60秒）。而本系统 AI 分析全套流程通常需要 **2到3分钟**（含多个工具调用），在 Vercel 上运行时必定触发 Timeout 错误，导致分析中断。

> **结论**: 如果强制通过 `vercel.json` 结合 `vercel-python` 打包器部署到 Vercel，您会看到静态页面，但在点击“运行分析”时会报错 `504 Gateway Timeout` 或 WebSocket 连接失败。

### ✅ 推荐部署方案

推荐使用支持 Docker 或长连接容器服务的云平台：

**方案一：Streamlit Community Cloud (免费、最简单)**
1. 将本项目推送到您的 GitHub 并在根目录包含 `requirements.txt`。
2. 登录 [share.streamlit.io](https://share.streamlit.io/)。
3. 点击 "New app"，选择对应的 GitHub 仓库和 `app.py`。
4. 在应用部署前的高级设置中，填入 `.env` 中的 `ANTHROPIC_API_KEY` 环境变量。

**方案二：Render 或 Zeabur**
1. 在项目根目录创建 `Dockerfile`。
2. 将代码推送到 GitHub，在 Render/Zeabur 中选择创建 Web Service。
3. 设置环境变量 `ANTHROPIC_API_KEY`。

---

## 技术架构

```
用户 → Streamlit Dashboard → AI Agent (brain.py)
                                   ↓
                            Claude Tool Use API
                              ↙    ↓    ↘
                        AKShare efinance SQLite
                        (快讯)  (行情)  (历史)
                              ↘    ↓    ↙
                          结构化 JSON 报告
                                   ↓
                            保存到数据库
                                   ↓
                          展示在 Dashboard
```

### 分析流程

1. 用户点击「运行分析」
2. 创建隔离的 Claude 对话会话
3. AI 自主决定调用哪些工具(最多 15 轮)
4. 每轮：Claude 发出工具调用请求 → 系统执行 → 返回结果
5. Claude 综合所有数据输出 JSON 报告
6. 系统校验报告格式（Pydantic）
7. 保存到 SQLite 数据库
8. Dashboard 展示结果

---

## 文件清单

| 文件 | 说明 |
|---|---|
| `PROJECT.md` | 项目 SSOT 总纲 |
| `USER_MANUAL.md` | 本手册 |
| `docs/2026-03-25-ai-stock-advisor-design.md` | 系统设计文档 |
| `.env.example` | 环境变量模板 |
| `.env` | 实际环境变量（不入 Git） |
| `requirements.txt` | Python 依赖 |
| `app.py` | Streamlit 入口 |
| `config/settings.py` | 全局配置 |
| `agent/brain.py` | AI 核心引擎 |
| `agent/tools.py` | 工具定义 |
| `agent/prompts.py` | System Prompt |
| `storage/database.py` | 数据库操作 |
| `storage/models.py` | 数据模型 |

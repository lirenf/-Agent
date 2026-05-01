# PaperMind — 高并发科研论文深度分析 Agent

> 结合学术深度与工程实践的 AI 驱动论文分析平台

---

## ✨ 功能特性

### 分析能力
| 模式 | 耗时 | 说明 |
|------|------|------|
| ⚡ 快速扫描 | ~2分钟 | 核心贡献、方法概述、创新评分 |
| 📊 标准分析 | ~5分钟 | 完整八维度解析（动机→方法→实验→影响） |
| 🔬 深度分析 | ~10分钟 | 批判性评估、工程视角、学术影响力预测 |

### 高并发架构
- **并发数**: 同时处理最多 5 篇论文（可配置）
- **控制机制**: `asyncio.Semaphore` + 前端 `Semaphore` 双层并发控制
- **流式输出**: Server-Sent Events (SSE) 逐字符实时返回
- **实时进度**: WebSocket 推送批量任务进度

### 输入方式
- 📝 **直接粘贴** 论文文本（中英文）
- 🔗 **URL 抓取** — 支持 arXiv / ACM / IEEE / Springer
- 📄 **PDF 上传** — 自动提取文本（非扫描件）

### 高级功能
- 🔍 **五维度专项分析**: 方法论 / 实验 / 创新性 / 影响力 / 局限性
- ⚖️ **多论文对比**: 2-6 篇论文横向比较报告
- 📋 **结果导出**: 一键复制 / 导出 Markdown
- 🌐 **中文优先**: 所有分析均以中文输出

---

## 🗂️ 项目结构

```
paper-analysis-agent/
├── backend/
│   ├── main.py                    # FastAPI 主入口
│   ├── agents/
│   │   ├── paper_analyzer.py      # 核心分析 Agent（流式）
│   │   ├── concurrent_processor.py # 并发批量处理器
│   │   └── prompts.py             # Prompt 模板库
│   ├── models/
│   │   └── schemas.py             # Pydantic 数据模型
│   ├── utils/
│   │   ├── pdf_extractor.py       # PDF 文本提取
│   │   └── web_scraper.py         # 异步网页抓取
│   └── requirements.txt
├── frontend/
│   ├── index.html                 # 主页面
│   ├── style.css                  # Dark Academic 主题
│   └── app.js                     # 前端逻辑
├── scripts/
│   ├── start.sh                   # Linux/macOS 启动
│   └── start.bat                  # Windows 启动
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

---

## 🚀 快速开始

### 方式一：直接运行（推荐）

**第一步：配置 API Key**
```bash
cp .env.example .env
# 编辑 .env，填入你的 Anthropic API Key
```

**第二步：启动**
```bash
# Linux / macOS
chmod +x scripts/start.sh
./scripts/start.sh

# Windows
scripts\start.bat
```

**第三步：访问**
打开浏览器访问 http://localhost:8000

---

### 方式二：手动运行

```bash
cd backend
pip install -r requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...  # Linux/macOS
set ANTHROPIC_API_KEY=sk-ant-...     # Windows

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 方式三：Docker

```bash
cp .env.example .env
# 填入 API Key

docker-compose up --build
```

---

## 📡 API 文档

启动后访问: http://localhost:8000/docs（Swagger UI）

### 主要端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/analyze/text` | 文本分析（SSE 流式） |
| `POST` | `/api/analyze/url`  | URL 抓取分析（SSE 流式） |
| `POST` | `/api/analyze/pdf`  | PDF 上传分析（SSE 流式） |
| `POST` | `/api/batch/analyze`| 批量并发分析 |
| `POST` | `/api/compare`      | 多论文对比（SSE 流式） |
| `WS`   | `/ws/{session_id}`  | 实时进度推送 |

### 请求示例

```python
import anthropic, httpx, json

# 文本分析（流式）
with httpx.stream("POST", "http://localhost:8000/api/analyze/text",
                  json={"text": "...", "mode": "deep"}) as r:
    for line in r.iter_lines():
        if line.startswith("data:") and line[5:].strip() != "[DONE]":
            chunk = json.loads(line[5:])
            if chunk["type"] == "delta":
                print(chunk["content"], end="", flush=True)
```

---

## ⚙️ 配置项

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ANTHROPIC_API_KEY` | 必填 | Anthropic API Key |
| `PORT` | `8000` | 服务端口 |

并发数可在 `backend/main.py` 中修改：
```python
processor = ConcurrentPaperProcessor(max_concurrency=5)  # 调整此值
```

---

## 🔧 技术栈

### 后端
- **FastAPI** — 高性能异步 Web 框架
- **Anthropic SDK** — Claude claude-sonnet-4 模型
- **asyncio** — Python 原生异步并发
- **aiohttp** — 异步 HTTP 客户端（网页抓取）
- **pdfplumber** — PDF 文本提取
- **WebSocket** — 实时进度推送

### 前端
- 原生 HTML/CSS/JS（无框架依赖）
- Dark Academic 设计风格
- Server-Sent Events 流式渲染
- 前端 Semaphore 并发控制

---

## 📝 使用技巧

1. **最佳分析效果**: 提供完整论文文本（含摘要+正文），避免仅提供摘要
2. **arXiv 论文**: 直接粘贴 arXiv 链接（如 `https://arxiv.org/abs/2310.06825`）
3. **深度分析**: 选择"深度分析"模式并勾选感兴趣的维度
4. **批量处理**: 队列中最多可添加任意数量论文，自动并发处理

---

## 📄 License

MIT License — 自由使用与修改

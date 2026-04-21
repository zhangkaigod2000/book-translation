# 📚 小说翻译系统 - Novel Translation System

基于多Agent架构的智能小说翻译系统，专为长篇小说人名一致性优化设计，支持多种LLM后端（vLLM/Ollama/OpenAI标准API）。

---

## ✨ 核心特性

### 🎯 翻译质量保障
- **🤖 多Agent协作**：6个专业Agent分工处理，对标CrewAI/LangGraph架构
- **📖 全局人名记忆库**：跨章节持久化存储，保证全书人名100%统一
- **🔍 自动章节识别**：智能识别99%网文格式，自动拆分章节
- **✅ 一致性保障机制**：三层防护确保人名零错乱

### 🌐 多语言支持
- **支持语言**：中文/英文/日文/韩文互译
- **语言切换**：上传页面可选、API调用可传参、.env配置文件

### 💾 数据持久化
- **📦 任务持久化**：SQLite数据库存储，后端重启后任务不丢失
- **📚 词典持久化**：每部小说的人名词典独立存储，支持断点续译
- **🔒 词典锁定**：关键人名可锁定，防止被LLM误改

### 🤖 多后端LLM支持
- **vLLM**：本地/远程vLLM服务（OpenAI兼容）
- **Ollama**：本地Ollama服务
- **OpenAI标准API**：硅基流动、DeepSeek、OpenAI、Azure OpenAI等

### 🎨 现代化UI
- Vue3 + Vite + Element Plus
- 实时翻译进度显示
- 章节列表状态实时更新
- 人名词典可视化编辑

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 Vue3 + Element Plus                 │
│  ┌─────────────┐  ┌───────────────┐  ┌───────────────────┐ │
│  │  上传页面    │  │  翻译控制台    │  │    人名词典管理    │ │
│  └─────────────┘  └───────────────┘  └───────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP接口
┌─────────────────────────────────────────────────────────────┐
│                   后端 FastAPI + SQLite                      │
│                      Supervisor Agent                        │
│  ┌─────────────┐  ┌───────────────┐  ┌───────────────────┐ │
│  │ ChapterSplit│  │EntityExtract  │  │GlossaryManager    │ │
│  │ 章节拆分    │  │ 实体提取      │  │  词典管理         │ │
│  └─────────────┘  └───────────────┘  └───────────────────┘ │
│  ┌─────────────┐  ┌───────────────┐  ┌───────────────────┐ │
│  │  Translate  │  │ Consistency   │  │  MergeOutput      │ │
│  │  核心翻译   │  │   一致性校验  │  │   合并导出        │ │
│  └─────────────┘  └───────────────┘  └───────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     LLM 后端（3选1）                          │
│  ┌─────────────┐  ┌───────────────┐  ┌───────────────────┐ │
│  │    vLLM     │  │    Ollama     │  │   OpenAI标准API   │ │
│  │ 本地/远程   │  │   本地部署     │  │ 硅基流动/DeepSeek │ │
│  └─────────────┘  └───────────────┘  └───────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 6个专业Agent

| Agent | 职责 | 关键功能 |
|-------|------|---------|
| **ChapterSplitAgent** | 自动识别并拆分小说章节 | 支持99%网文格式：第X章、Chapter X、卷X第X章等 |
| **EntityExtractAgent** | 提取所有人名、地名、势力名等实体 | LLM智能识别 + 自动分类（person/location/organization等） |
| **GlossaryManagerAgent** | 维护全局唯一人名词典 | 别名合并、新人名入库、旧人名复用 |
| **TranslateAgent** | 核心翻译Agent | 强制使用全局词典、支持重试机制、章节间延迟 |
| **ConsistencyCheckAgent** | 翻译后一致性校验 | 自动检查人名一致性，不一致自动重译（最多3次） |
| **MergeOutputAgent** | 合并所有章节译文 | 按原顺序合并，生成完整翻译小说txt |

---

## 📋 技术栈

### 后端
- **Python 3.9+**
- **FastAPI**：高性能异步Web框架
- **SQLite**：轻量级数据库，任务和词典持久化
- **httpx**：异步HTTP客户端，支持超时配置

### 前端
- **Vue 3.3+**：Composition API
- **Vite 5**：快速构建工具
- **Vue Router 4**：前端路由
- **Element Plus 2**：UI组件库
- **Axios**：HTTP客户端

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- Node.js 16+
- 以下LLM服务任选其一：
  - vLLM服务（本地或远程）
  - Ollama（本地）
  - OpenAI标准API密钥（硅基流动/DeepSeek等）

### 2. 启动后端服务

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，选择LLM后端并配置

# 启动服务
python main.py
```

后端将在 `http://localhost:5020` 启动

### 3. 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:5021` 启动

### 4. 配置LLM服务

选择以下三种方式之一：

#### 方式A：vLLM（推荐自建GPU服务器）

```bash
# 启动vLLM服务
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen-7B-Chat \
    --port 8080
```

配置 `.env`：
```env
LLM_BACKEND=vllm
VLLM_BASE_URL=http://localhost:8080/v1
VLLM_MODEL_NAME=Qwen-7B-Chat
VLLM_API_KEY=sk-local
```

#### 方式B：Ollama（本地开发测试）

```bash
# 安装Ollama并启动
ollama serve

# 拉取模型
ollama pull qwen2.5:7b
```

配置 `.env`：
```env
LLM_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=qwen2.5:7b
```

#### 方式C：OpenAI标准API（硅基流动/DeepSeek等）

**硅基流动 SiliconFlow**：
```env
LLM_BACKEND=openai
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
```

**DeepSeek**：
```env
LLM_BACKEND=openai
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL_NAME=deepseek-chat
```

**OpenAI**：
```env
LLM_BACKEND=openai
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL_NAME=gpt-4o-mini
```

---

## ⚙️ 完整配置说明

### 后端配置 (.env)

```env
# ========== 服务基础配置 ==========
SERVER_HOST=0.0.0.0
SERVER_PORT=5020
CORS_ORIGIN=http://localhost:5021

# ========== LLM 后端选择 ==========
# 可选值: vllm, ollama, openai
LLM_BACKEND=openai

# ========== vLLM 推理配置 ==========
VLLM_BASE_URL=http://localhost:8080/v1
VLLM_MODEL_NAME=Qwen-7B-Chat
VLLM_API_KEY=sk-local

# ========== Ollama 推理配置 ==========
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=qwen2.5:7b

# ========== OpenAI 标准 API 配置 ==========
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL_NAME=Qwen/Qwen2.5-7B-Instruct

# ========== 通用 LLM 配置 ==========
LLM_TEMPERATURE=0.05      # 温度越低，人名越稳定
LLM_MAX_TOKENS=60000      # 最大输出token
LLM_TIMEOUT=1200          # 请求超时时间（秒）

# ========== 小说翻译核心配置 ==========
SOURCE_LANGUAGE=Chinese
TARGET_LANGUAGE=English
AUTO_DETECT_CHAPTER=true          # 自动识别章节
GLOBAL_GLOSSARY_MEMORY=true       # 开启全局人名记忆
FORCE_NAME_CONSISTENCY=true       # 强制人名一致
MERGE_ALIAS=true                  # 自动合并别名
MAX_CHUNK_PER_CHAPTER=8000        # 单章分块大小
CONSISTENCY_CHECK_ENABLE=true     # 开启一致性校验

# ========== 章节识别正则配置 ==========
CHAPTER_REGEX=^第.{1,5}章.*$
TITLE_KEEP_FORMAT=true

# ========== 数据库持久化 ==========
DATABASE_URL=sqlite:///./novel_translate.db
SAVE_GLOSSARY_TO_DB=true
```

### 前端配置 (.env)

```env
VITE_API_BASE_URL=http://localhost:5020/api
```

---

## 🌐 支持的语言对

- 🇨🇳 中文 (Chinese)
- 🇺🇸 英文 (English)
- 🇯🇵 日文 (Japanese)
- 🇰🇷 韩文 (Korean)

**切换方式**：
1. 上传页面下拉选择
2. 修改 `.env` 的 `SOURCE_LANGUAGE` 和 `TARGET_LANGUAGE`
3. API调用时传入参数

---

## 🎯 使用流程

### Web界面（推荐）

1. **上传小说**
   - 访问 `http://localhost:5021`
   - 上传 `.txt` 格式小说
   - 选择源语言和目标语言
   - 点击"上传并识别章节"

2. **查看章节**
   - 系统自动拆分所有章节
   - 显示章节总数和标题列表

3. **开始翻译**
   - 进入翻译控制台
   - 点击"开始翻译"
   - 实时查看进度和章节状态

4. **管理人名词典**（可选）
   - 访问"人名词典"页面
   - 查看/编辑/锁定/删除词条
   - 修改后影响后续未翻译章节

5. **下载译文**
   - 翻译完成后点击"下载译文"
   - 获取完整翻译小说 `.txt` 文件

### API调用

```bash
# 1. 上传小说
curl -X POST http://localhost:5020/api/novel/upload \
  -F "file=@novel.txt"

# 2. 识别章节
curl -X POST "http://localhost:5020/api/novel/auto-chapter?task_id=xxx"

# 3. 开始翻译
curl -X POST http://localhost:5020/api/translate/start \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "xxx",
    "source_language": "Chinese",
    "target_language": "English"
  }'

# 4. 查询进度
curl "http://localhost:5020/api/translate/progress?task_id=xxx"

# 5. 下载结果
curl "http://localhost:5020/api/novel/download?task_id=xxx" -o translated.txt
```

---

## 🔧 核心机制详解

### 人名一致性保障（三层防护）

```
第一层：提取阶段
├── EntityExtractAgent 扫描原文
├── 自动识别所有人名、地名、势力名
└── 已有名字复用，新人名入库

第二层：翻译Prompt阶段
├── 将全局词典注入LLM系统提示词
├── LLM强制使用词典中的翻译
└── 禁止私自修改或创造新人名

第三层：校验阶段
├── ConsistencyCheckAgent 二次检查
├── 对比原文和译文的人名
└── 不一致自动重译（最多3次）
```

### 词典持久化机制

```
翻译第1章
    ↓
提取人名A → 翻译为Alice → 保存到内存 + SQLite
    ↓
翻译第2章
    ↓
发现人名A → 查询SQLite → 使用Alice
    ↓
程序重启
    ↓
恢复翻译第3章
    ↓
从SQLite加载词典 → 发现人名A = Alice → 保持一致
```

### 任务持久化机制

```
上传小说 → 任务保存到SQLite
    ↓
开始翻译 → 实时更新进度到SQLite
    ↓
后端重启 → 自动恢复未完成任务
    ↓
查询进度 → 从SQLite读取 → 继续翻译
```

---

## 📂 项目结构

```
book-trans/
├── backend/
│   ├── .env                      # 后端配置
│   ├── .env.example              # 配置示例
│   ├── main.py                   # FastAPI入口
│   ├── requirements.txt          # Python依赖
│   ├── novel_translate.db        # SQLite数据库
│   └── src/
│       ├── core/
│       │   ├── config.py         # 配置管理
│       │   └── vllm_client.py    # 统一LLM客户端（vLLM/Ollama/OpenAI）
│       ├── agents/
│       │   ├── supervisor.py     # 总调度Agent + 任务恢复
│       │   ├── chapter_split.py  # 章节拆分
│       │   ├── entity_extract.py # 实体提取
│       │   ├── glossary_manager.py # 词典管理
│       │   ├── translate.py      # 翻译Agent（含重试机制）
│       │   ├── consistency_check.py # 一致性校验
│       │   └── merge_output.py   # 合并导出
│       ├── global_memory/
│       │   └── novel_glossary.py # 人名词典（含持久化）
│       └── db/
│           └── database.py       # SQLite数据库操作
├── frontend/
│   ├── .env                      # 前端配置
│   ├── package.json              # Node.js依赖
│   ├── vite.config.js            # Vite配置
│   └── src/
│       ├── main.js               # 应用入口
│       ├── App.vue               # 根组件（显示LLM后端信息）
│       ├── api/request.js        # API封装
│       └── views/
│           ├── Home.vue          # 首页（上传+语言选择）
│           ├── Translate.vue     # 翻译控制台（实时进度+章节状态）
│           └── Glossary.vue      # 词典管理页
└── README.md                     # 本文档
```

---

## 💡 最佳实践

### 1. 选择合适的LLM后端

| 场景 | 推荐后端 | 说明 |
|------|---------|------|
| 有GPU服务器 | vLLM | 速度快、成本低、私有化部署 |
| 本地开发测试 | Ollama | 完全免费、离线可用 |
| 追求便利性 | 硅基流动 | 免部署、按量付费、模型丰富 |
| 高质量翻译 | DeepSeek | 中文能力强、价格适中 |

### 2. 优化翻译质量

```env
# 温度设置（越低人名越稳定）
LLM_TEMPERATURE=0.05   # 推荐 0.01-0.1

# 分块大小（影响翻译连贯性）
MAX_CHUNK_PER_CHAPTER=8000  # 推荐 4000-12000

# 开启一致性校验
CONSISTENCY_CHECK_ENABLE=true
```

### 3. 处理高并发场景

```env
# 增加超时时间
LLM_TIMEOUT=1800        # 30分钟

# 章节间延迟（避免LLM服务器过载）
# 代码中已内置5秒延迟
```

### 4. 锁定关键人名

1. 先翻译前3-5章
2. 进入词典管理页面
3. 检查关键人物翻译
4. 锁定准确的人名翻译
5. 继续后续章节翻译

---

## ❓ 常见问题

### Q: 后端重启后任务会丢失吗？

**A**: 不会！任务和词典都保存在SQLite数据库中，后端重启后会自动恢复未完成的任务和词典。

### Q: 如何更换LLM后端？

**A**: 修改 `.env` 文件：
```env
LLM_BACKEND=openai  # 或 vllm / ollama
```
然后重启后端即可。

### Q: 硅基流动/DeepSeek怎么配置？

**A**: 
```env
LLM_BACKEND=openai
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
```

### Q: 翻译速度慢怎么办？

**A**: 
- 使用更大的 `MAX_CHUNK_PER_CHAPTER` 减少请求次数
- 使用更快的LLM后端（如vLLM本地部署）
- 检查网络连接和LLM服务器负载

### Q: 人名翻译不一致怎么办？

**A**: 
1. 在词典管理页面手动修正
2. 锁定该人名
3. 重新翻译后续章节

### Q: 支持哪些小说格式？

**A**: 目前仅支持 `.txt` 格式，其他格式请先转换为txt。

---

## 🛠️ 开发说明

### 本地开发

```bash
# 后端热重载
cd backend
pip install uvicorn[standard]
uvicorn main:app --reload --port 5020

# 前端热重载
cd frontend
npm run dev
```

### 生产部署

```bash
# 构建前端
cd frontend && npm run build

# 部署后端
cd backend
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5020
```

---

## 📡 API接口文档

### 小说管理
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/novel/upload` | POST | 上传小说文件 |
| `/api/novel/auto-chapter` | POST | 自动识别章节 |
| `/api/novel/chapters` | GET | 查看章节列表 |
| `/api/novel/download` | GET | 下载翻译结果 |

### 翻译控制
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/translate/start` | POST | 开始翻译 |
| `/api/translate/progress` | GET | 获取翻译进度 |

### 词典管理
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/glossary/global` | GET | 查询全局词典（支持task_id筛选） |
| `/api/glossary/edit` | POST | 编辑词条 |
| `/api/glossary/lock` | POST | 锁定词条 |
| `/api/glossary/unlock` | POST | 解锁词条 |
| `/api/glossary/delete` | DELETE | 删除词条 |

### 系统信息
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/llm/backend-info` | GET | 获取当前LLM后端信息 |

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [CrewAI](https://github.com/joaomdmoura/crewAI) - Agent协作框架灵感
- [LangGraph](https://github.com/langchain-ai/langgraph) - 工作流编排参考
- [vLLM](https://github.com/vllm-project/vllm) - 高效推理引擎
- [Ollama](https://ollama.com/) - 本地LLM部署
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Element Plus](https://element-plus.org/) - Vue 3 UI组件库

---

**⭐ 如果这个项目对你有帮助，欢迎给个Star！**

**📧 问题反馈**：请在GitHub提交Issue

**💬 技术讨论**：欢迎参与社区讨论

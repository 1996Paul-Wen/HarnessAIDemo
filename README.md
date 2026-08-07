# HarnessAIDemo - AI Agent Harness 工程演示

> 一个全面的 AI Agent Harness 工程 Demo，帮助你理解工业级 AI 应用的核心架构。

## 项目概述

本项目使用 HuggingFace 上的小模型 (Qwen2.5-0.5B-Instruct)，通过从零实现一个完整的 AI Agent Harness，展示以下核心概念：

| 模块 | 概念 | 关键文件 |
|------|------|---------|
| Agent Loop | Agent 执行循环（LLM 调用 -> 工具调用 -> 循环） | `harness/agent/base.py` |
| Context Management | 上下文组装与管理 | `harness/context/manager.py` |
| Memory System | 短期记忆 + 长期记忆 | `harness/memory/` |
| Tool System | 工具注册、调用、执行 | `harness/tools/` |
| MCP Protocol | Model Context Protocol 实现 | `harness/mcp/protocol.py` |
| Skill System | Markdown 定义的可复用技能 | `harness/skill/` |
| Session Management | 多会话隔离管理 | `harness/session/manager.py` |
| Multi-Agent | 多 Agent 协同与编排 | `harness/agent/orchestrator.py` |

---

## 快速开始

### 1. 环境准备

```bash
# 运行 setup 脚本（自动创建虚拟环境并安装依赖）
bash setup.sh

# 激活虚拟环境
source .venv/bin/activate
```

### 2. 使用 Mock 后端快速体验（无需下载模型）

```bash
# 设置使用 Mock LLM（基于模式匹配，无需 GPU）
export HARNESS_LLM_BACKEND=mock

# 运行各个 Demo
python run.py chat          # 交互式聊天
python run.py agent         # 单 Agent 工具调用
python run.py multi-agent   # 多 Agent 编排
python run.py mcp           # MCP 协议演示
python run.py skills        # 技能系统演示
python run.py session       # 多会话管理演示
```

### 3. 使用真实模型

```bash
# 默认使用 Qwen2.5-0.5B-Instruct（约 1GB，首次运行自动下载）
python run.py chat

# 指定其他模型
export HARNESS_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
python run.py agent
```

### 4. 独立 Demo 脚本

```bash
python demos/demo_chat.py          # 聊天 Demo
python demos/demo_agent.py         # Agent 工具调用 Demo
python demos/demo_multi_agent.py   # 多 Agent Demo
python demos/demo_mcp.py           # MCP 协议 Demo
python demos/demo_skills.py        # 技能系统 Demo
python demos/demo_session.py       # 多会话 Demo
```

---

## 项目结构

```
HarnessAIDemo/
├── run.py                     # 主入口
├── setup.sh                   # 环境初始化脚本
├── requirements.txt           # Python 依赖
├── pyproject.toml             # 项目配置
│
├── harness/                   # 核心 Harness 框架
│   ├── config.py              #   全局配置
│   ├── cli.py                 #   CLI 命令行界面
│   │
│   ├── llm/                   # LLM 引擎层
│   │   └── engine.py          #     模型抽象 + Transformers/Mock 后端
│   │
│   ├── tools/                 # 工具系统
│   │   ├── base.py            #     BaseTool 抽象基类
│   │   ├── registry.py        #     ToolRegistry 注册表
│   │   └── builtin.py         #     内置工具 (Calculator, DateTime, FileOps)
│   │
│   ├── memory/                # 记忆系统
│   │   ├── base.py            #     BaseMemory 抽象基类
│   │   ├── short_term.py      #     短期记忆 (Buffer/FIFO)
│   │   ├── long_term.py       #     长期记忆 (TF-IDF 检索 + 持久化)
│   │   └── hybrid.py          #     混合记忆 (Short + Long)
│   │
│   ├── context/               # 上下文管理
│   │   └── manager.py         #     ContextManager 上下文组装
│   │
│   ├── mcp/                   # MCP 协议
│   │   └── protocol.py        #     Server/Client/JSON-RPC 实现
│   │
│   ├── skill/                 # 技能系统
│   │   ├── base.py            #     Skill 数据类
│   │   └── loader.py          #     SKILL.md 解析与加载
│   │
│   ├── agent/                 # Agent 系统
│   │   ├── base.py            #     BaseAgent + Agent Loop 核心实现
│   │   ├── chat.py            #     ChatAgent 对话 Agent
│   │   ├── task.py            #     TaskAgent 任务 Agent
│   │   └── orchestrator.py    #     MultiAgentOrchestrator 多 Agent 编排
│   │
│   └── session/               # 会话管理
│       └── manager.py         #     SessionManager 多会话管理
│
├── demos/                     # 演示脚本
│   ├── demo_chat.py
│   ├── demo_agent.py
│   ├── demo_multi_agent.py
│   ├── demo_mcp.py
│   ├── demo_skills.py
│   ├── demo_session.py
│   └── skills/                # 示例技能
│       ├── summarizer/SKILL.md
│       └── translator/SKILL.md
│
└── README.md                  # 本文档
```

---

## 核心概念详解

### 1. Agent Loop（Agent 循环）— `harness/agent/base.py`

Agent Loop 是整个 Harness 的**核心**。它是让 LLM 从"一问一答"变成"能自主完成任务的 Agent"的关键：

```
用户输入
    ↓
┌──→ 构建上下文 (System Prompt + Memory + Tools + History)
│       ↓
│   调用 LLM 生成响应
│       ↓
│   ┌─ 有 Tool Call？──Yes──→ 执行工具 → 把结果加入上下文 ─┐
│   │                                                        │
│   └─ No ─→ 返回最终答案 → 存入 Memory → 结束             │
│                                                            │
└────────────────────────────────────────────────────────────┘
                    (循环继续，直到给出最终答案)
```

**关键设计：**
- `max_iterations` 防止无限循环
- 每次循环都将工具结果作为 `Observation` 消息反馈给 LLM
- LLM 看到工具结果后决定是否需要继续调用工具

### 2. Context Management（上下文管理）— `harness/context/manager.py`

Context Manager 负责**每次 LLM 调用前的上下文组装**：

```
最终 Prompt = System Prompt
            + Tool 使用说明和工具列表
            + 相关历史记忆 (从 Long-term Memory 检索)
            + 最近对话历史 (从 Short-term Memory 获取)
            + 当前用户输入
```

**关键设计：**
- LLM 有有限的 context window，需要智能选择哪些内容放进去
- Token 估算用于控制上下文大小
- 工具描述动态注入 system prompt

### 3. Memory System（记忆系统）— `harness/memory/`

三层记忆架构，模拟人类记忆系统：

| 层级 | 实现 | 类比 | 用途 |
|------|------|------|------|
| ShortTermMemory | 有界 Buffer (FIFO) | 工作记忆 | 保存最近 N 条对话 |
| LongTermMemory | TF-IDF 检索 + JSON 持久化 | 长期记忆 | 跨会话持久化知识 |
| HybridMemory | Short + Long 组合 | 完整记忆 | 生产推荐方案 |

**长期记忆检索流程：**
1. 用户输入作为 query
2. 对长期记忆中的每条记录计算 TF-IDF 相似度
3. 返回 top-K 最相关的记忆
4. 注入到 prompt 中作为上下文

### 4. Tool System（工具系统）— `harness/tools/`

```
BaseTool (抽象基类)
  ├── name: 工具名 (LLM 通过名字调用)
  ├── description: 描述 (展示给 LLM)
  ├── parameters: 参数说明
  └── execute(**kwargs) -> ToolResult

ToolRegistry (注册表)
  ├── register(tool): 注册工具
  ├── execute(name, args): 按名称执行
  └── get_tools_description(): 生成 prompt 文本
```

**内置工具：**
- `calculator`: 安全的数学表达式计算
- `datetime`: 获取当前日期/时间
- `file_ops`: 文件列表和读取（只读，安全）

### 5. MCP Protocol（Model Context Protocol）— `harness/mcp/protocol.py`

MCP 是 AI 工具调用的标准化协议，类似于 USB 之于硬件设备：

```
Agent (Client)  ←──JSON-RPC 2.0──→  MCP Server
                                      ├── tools/     (可调用的函数)
                                      ├── resources/ (可读取的数据源)
                                      └── prompts/   (可复用的模板)
```

**本项目实现的 MCP 方法：**
- `tools/list` - 列出所有工具
- `tools/call` - 调用指定工具
- `resources/read` - 读取资源
- `prompts/get` - 获取 prompt 模板

**为什么 MCP 重要：**
- 标准化：不同 AI 应用可以共享同一套工具
- 解耦：工具提供方和 AI 应用独立演进
- 安全：通过协议层控制权限和访问

### 6. Skill System（技能系统）— `harness/skill/`

技能是通过 Markdown 文件定义的 Agent 能力模块：

```
demos/skills/
└── summarizer/
    └── SKILL.md
        ├── --- (YAML frontmatter: name, description, tags)
        └── # Instructions (详细的执行指令)
```

**Skill 工作流程：**
1. `SkillLoader.discover()` 扫描 skills 目录
2. `SkillLoader.load()` 解析 SKILL.md 的 frontmatter 和指令
3. `Skill.apply_to_prompt()` 将技能指令注入到 prompt 中

### 7. Session Management（会话管理）— `harness/session/manager.py`

```
SessionManager
  ├── create_session("Coding")    → Session(id="a1b2", messages=[...])
  ├── create_session("Research")  → Session(id="c3d4", messages=[...])
  ├── switch_session("a1b2")      → 切换到 Coding 会话
  ├── list_sessions()             → 列出所有会话
  └── delete_session("c3d4")      → 删除 Research 会话
```

每个 Session 独立维护：
- 对话历史 (messages)
- 元数据 (标题、创建时间)
- 持久化存储 (JSON 文件)

### 8. Multi-Agent Orchestration（多 Agent 编排）— `harness/agent/orchestrator.py`

```
用户请求 → Orchestrator (Supervisor)
               │
               ├── MathAgent   (有 Calculator 工具)
               ├── TimeAgent   (有 DateTime 工具)
               └── ChatAgent   (通用对话)
```

**编排流程：**
1. Supervisor 接收用户请求
2. 使用 LLM 判断哪个 Agent 最适合
3. 委派给对应 Agent 执行
4. 返回 Agent 的执行结果

---

## 配置说明

通过环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HARNESS_LLM_BACKEND` | `transformers` | LLM 后端: `transformers` 或 `mock` |
| `HARNESS_MODEL_NAME` | `Qwen/Qwen2.5-0.5B-Instruct` | HuggingFace 模型名 |
| `HARNESS_MAX_TOKENS` | `512` | 每次生成最大 token 数 |
| `HARNESS_TEMPERATURE` | `0.7` | 采样温度 |
| `HARNESS_DEVICE` | `auto` | 运行设备: `cpu`, `cuda`, `mps` |

---

## 扩展指南

### 添加自定义工具

```python
from harness.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "My custom tool does X"
    parameters = {"input": "string - the input data"}

    def execute(self, input="", **kw):
        result = f"Processed: {input}"
        return ToolResult(True, result)

# 注册使用
registry = ToolRegistry()
registry.register(MyTool())
```

### 添加自定义 Skill

创建目录 `my_skills/my_skill/SKILL.md`:

```markdown
---
name: My Skill
description: Description of the skill
tags: [tag1, tag2]
---

# Instructions
Detailed instructions for the agent...
```

### 添加 MCP Server

```python
from harness.mcp.protocol import MCPServer

server = MCPServer("my-server")
server.register_tool(
    name="my_mcp_tool",
    description="A tool exposed via MCP",
    input_schema={"param": "string"},
    handler=lambda param="": f"Result for {param}",
)
```

---

## 技术栈

- **Python 3.11** - 运行时
- **PyTorch + Transformers** - 模型推理
- **Qwen2.5-0.5B-Instruct** - 默认 LLM (HuggingFace)
- **MockBackend** - 无 GPU 的测试后端
- **TF-IDF** - 长期记忆检索
- **JSON-RPC 2.0** - MCP 协议实现

---

## 学习路径建议

1. **先跑 Mock Demo**: `HARNESS_LLM_BACKEND=mock python run.py session` 理解会话管理
2. **再看 MCP Demo**: `python run.py mcp` 理解工具协议
3. **然后看 Skills Demo**: `python run.py skills` 理解技能加载
4. **核心 - Agent Loop**: 仔细阅读 `harness/agent/base.py`，这是整个系统的核心
5. **进阶 - 真实模型**: 切换到 transformers 后端，观察真实 LLM 的工具调用行为
6. **扩展**: 添加自己的工具、技能、MCP Server

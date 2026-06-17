# hello-agent

AI 智能体（Agent）框架学习工作区，收录多个 Agent 框架的 Demo 项目。

---

## 📂 目录结构

```
hello-agent/
├── .env                  # 环境变量（API Key 等，不纳入版本控制）
├── .venv/                # Python 虚拟环境
├── AutoGen/              # Microsoft AutoGen 框架 Demo
│   ├── README.md
│   ├── App.py
│   ├── AgentRoles.py
│   ├── ModeClient.py
│   ├── TeamCollaborationProcess.py
│   ├── FileExporter.py
│   └── result/           # 智能体输出归档
└── AgentScope/           # 阿里 AgentScope 2.x 框架 Demo
    ├── README.md
    ├── test.py
    └── ThreeKingdomsWerewolf_Test/
        ├── main.py       # 主入口
        ├── game.py       # 游戏引擎
        ├── models.py     # 结构化输出模型
        ├── prompts.py    # 角色提示词
        └── model_config.json  # 历史参考
```

## 🚀 已完成的框架

| 框架 | 目录 | 说明 |
|------|------|------|
| **AutoGen** | [`AutoGen/`](./AutoGen/) | 多智能体团队协作——产品经理 + 工程师 + 代码审查员 |
| **AgentScope** | [`AgentScope/`](./AgentScope/) | 三国狼人杀博弈——预言家/女巫/狼人/村民自主推理决出胜负 |

## ⚙️ 环境准备

```powershell
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# AutoGen 依赖
pip install autogen-agentchat "autogen-ext[openai]" python-dotenv

# AgentScope 依赖
pip install agentscope python-dotenv
```

在 `.env` 中配置 API Key：
```
OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=sk-xxx
DASHSCOPE_API_KEY=sk-xxx
```
```

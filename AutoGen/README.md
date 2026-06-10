# AutoGen — 多智能体软件开发团队

基于 Microsoft AutoGen 框架实现的多智能体协作 Demo：由 **产品经理 → 工程师 → 代码审查员 → 用户代理** 四个角色组成的软件开发团队，自动完成从需求分析到代码交付的全流程。

---

## 🏗 架构

```
App.py                         # 主入口：初始化 → 组队 → 执行任务
  ├── ModeClient.py            # 模型客户端工厂（支持 OpenAI / DeepSeek 等）
  ├── AgentRoles.py            # 定义 4 个 Agent 角色及 system prompt
  ├── TeamCollaborationProcess.py  # 团队组建（RoundRobin 轮询群聊）
  └── FileExporter.py          # 输出归档（代码提取 + 对话记录）
```

### 协作流程

```
用户任务
  → ProductManager（需求分析、模块划分）
    → Engineer（编写代码，用 ```python 输出）
      → CodeReviewer（审查代码质量）
        → UserProxy（验收评价 / TERMINATE）
          → 循环直至终止
```

## 📁 文件说明

| 文件 | 职责 |
|------|------|
| `App.py` | 主入口，串联所有模块，启动异步协作流程 |
| `ModeClient.py` | 模型客户端工厂，支持 OpenAI 原生模型 & DeepSeek 等非 OpenAI 模型 |
| `AgentRoles.py` | 定义 ProductManager / Engineer / CodeReviewer / UserProxy 四个角色 |
| `TeamCollaborationProcess.py` | 轮询群聊（RoundRobinGroupChat）配置，终止条件为 TERMINATE |
| `FileExporter.py` | 从对话流中提取代码块并保存为文件，同时导出完整对话记录 |

## 🚀 运行

```powershell
# 在 AutoGen 目录下
python App.py
```

运行后：
1. 智能体自动协作，控制台实时输出对话
2. 结果自动归档到 `result/` 目录

## 📂 输出结构

```
result/20260610_1722/
├── conversation.md              # 完整多轮对话记录
├── code/                        # 提取的代码文件（仅 Engineer）
│   ├── app.py
│   └── run.sh
└── agents/                      # 各智能体独立输出
    ├── 01_ProductManager.md
    ├── 02_Engineer.md
    ├── 03_CodeReviewer.md
    └── 04_UserProxy.md
```

## 🔧 扩展厂商

在 `ModeClient.py` 的 `PROVIDER_CONFIGS` 中添加新厂商即可：

```python
"zhipu": {
    "needs_model_info": True,
    "env_key": "ZHIPU_API_KEY",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "default_model": "glm-4",
}
```

非 OpenAI 模型还需在 `NON_OPENAI_MODEL_INFO` 中声明模型能力。

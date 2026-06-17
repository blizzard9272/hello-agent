# AgentScope — 三国狼人杀多智能体博弈

基于阿里 AgentScope 2.x 框架实现的多智能体博弈 Demo：以三国武将为角色，实现完整的 **狼人杀** 游戏逻辑——黑夜密谋、预言查验、女巫用药、白天辩论、放逐投票，智能体自主推理决出胜负。

---

## 🏗 架构

```
ThreeKingdomsWerewolf_Test/
├── main.py              # 主入口：初始化模型 → 创建游戏 → 启动循环
├── game.py              # 游戏引擎：回合控制 + 角色行动 + 胜负裁决
├── models.py            # Pydantic 结构化输出模型（LLM 回复解析）
├── prompts.py           # 角色系统提示词（武将人格 + 狼人杀规则）
└── model_config.json    # 历史参考（2.x 已改为代码创建模型）
```

### 游戏流程

```
游戏开始
  ↓
┌─ 黑夜阶段 ──────────────────────────────────┐
│  1. 狼人密谋 → 秘密频道商议 → 投票击杀目标      │
│  2. 预言家验人 → 查验一名玩家真实阵营            │
│  3. 女巫用药 → 解药救人 / 毒药杀人 / 不操作      │
└──────────────────────────────────────────────┘
  ↓
┌─ 白天阶段 ──────────────────────────────────┐
│  4. 公布死讯 → 法官宣布昨夜死亡情况              │
│  5. 公开辩论 → 两轮自由发言（并发 + 互传）        │
│  6. 放逐投票 → 全员投票 → 最高票出局              │
└──────────────────────────────────────────────┘
  ↓
胜负判定（狼人全灭 → 好人胜 / 狼人 ≥ 好人 → 狼人胜）
  ↓
下一轮 / 游戏结束
```

## 📁 文件说明

| 文件 | 职责 |
|------|------|
| `main.py` | 主入口，创建模型实例（DashScope/Ollama），配置玩家阵营，启动游戏 |
| `game.py` | 游戏引擎核心，包含：`_werewolf_night_action` / `_seer_night_action` / `_witch_night_action` / `_public_discussion` / `_public_vote` / `check_victory_conditions` |
| `models.py` | Pydantic 结构化输出模型：`DiscussionModelCN` / `VoteModelCN` / `SeerActionModelCN` / `WitchActionModelCN`，配合 `_build_json_prompt()` 和 `_parse_structured_response()` 实现 LLM 回复的确定性解析 |
| `prompts.py` | 动态生成角色提示词，融合"三国武将性格"与"狼人杀职位规则"，含场外信息禁止条款 |

## 🚀 运行

```powershell
# 在 AgentScope/ThreeKingdomsWerewolf_Test 目录下
python main.py
```

运行前确保：
1. 在 `../../.env` 中配置 `DASHSCOPE_API_KEY`
2. 或在 `main.py` 中切换为 Ollama 本地模型

## 🎮 玩家配置

在 `main.py` 中修改 `mock_players` 即可自定义：

```python
mock_players = [
    {"name": "诸葛亮", "role": "预言家"},
    {"name": "关羽",   "role": "狼人"},
    {"name": "董卓",   "role": "平民"},
    {"name": "刘备",   "role": "狼人"},
    {"name": "刘禅",   "role": "女巫"},
    {"name": "张飞",   "role": "平民"},
]
```

支持的角色：`预言家` / `女巫` / `狼人` / `村民`（或 `平民`）

## 🔧 AgentScope 1.x → 2.x 迁移要点

| 1.x | 2.x |
|-----|-----|
| `agentscope.init(model_configs=".json")` | 代码直接创建模型实例 |
| `DialogAgent(sys_prompt=..., model_config_name=...)` | `Agent(system_prompt=..., model=model)` |
| `MsgHub` / `fanout_pipeline` 群发/并发 | `asyncio.gather(*[agent.reply(...)])` 手动编排 |
| `agent.observe(msg)` | `await agent.observe(msg)`（async 协程） |

## 🛠 结构化输出设计

`models.py` 定义了 4 种 Pydantic 模型，替代自由文本 + 字符串匹配：

| 模型 | 使用场景 | 关键字段 |
|------|---------|---------|
| `DiscussionModelCN` | 狼人讨论 / 白天辩论 | `thought`, `suggested_target` |
| `VoteModelCN` | 狼人投票 / 白天放逐 | `target_name`, `reason` |
| `SeerActionModelCN` | 预言家查验 | `target_name` |
| `WitchActionModelCN` | 女巫用药 | `use_antidote`, `use_poison`, `target_name` |

解析容错链：直接 JSON → Markdown 代码块提取 → 正则兜底 → 字符串回退。

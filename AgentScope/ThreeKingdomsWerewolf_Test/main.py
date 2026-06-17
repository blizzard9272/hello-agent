import asyncio
import os
from dotenv import load_dotenv

# AgentScope 2.x：不再使用 agentscope.init()，改为直接创建模型实例
from agentscope.model import DashScopeChatModel, OllamaChatModel
from agentscope.credential import DashScopeCredential, OllamaCredential
from game import ThreeKingdomsWerewolfGame

async def main():
    # 加载 .env 环境变量
    dotenv_path = os.path.join(os.path.dirname(__file__), "../../.env")
    if load_dotenv(dotenv_path):
        print("[系统环境] 成功读取上一层目录的 .env 配置文件")
    else:
        print("[系统警告] 未找到 .env 文件，请检查路径")

    # ============================================================
    # AgentScope 2.x 模型创建方式（二选一）
    # ============================================================

    # 方案一：DashScope 通义千问模型（推荐）
    model = DashScopeChatModel(
        credential=DashScopeCredential(
            api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
        ),
        model="qwen3.6-plus",
        parameters=DashScopeChatModel.Parameters(
            temperature=0.4,
            max_tokens=1024,
        ),
    )

    # 方案二：本地 Ollama 模型（取消注释以使用）
    # model = OllamaChatModel(
    #     credential=OllamaCredential(
    #         host="http://localhost:11434/v1"
    #     ),
    #     model="deepseek-r1:7b",
    #     parameters=OllamaChatModel.Parameters(
    #         temperature=0.3,
    #     ),
    # )

    # 模拟一个 5 人的精简局配置
    mock_players = [
        {"name": "诸葛亮", "role": "预言家"},
        {"name": "关羽", "role": "狼人"},
        {"name": "董卓", "role": "平民"},
        {"name": "刘备", "role": "狼人"},
        {"name": "刘禅", "role": "女巫"},
        {"name": "张飞", "role": "平民"},
    ]
    
    # 实例化游戏（传入模型实例）
    game = ThreeKingdomsWerewolfGame(player_configs=mock_players, model=model)
    
    # 启动游戏引擎
    await game.start_game()

if __name__ == "__main__":
    asyncio.run(main())
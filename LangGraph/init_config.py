import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.chat_models.tongyi import ChatTongyi
from tavily import TavilyClient

# 加载 .env 文件中的环境变量（从项目根目录）
# load_dotenv() 默认会从当前工作目录开始向上查找 .env 文件，直到找到为止
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 初始化模型
# 我们将使用这个 llm 实例来驱动所有节点的智能

# 推荐方式：使用 ChatOpenAI + 百炼兼容端点，支持模型广场的完整模型ID
# 在 .env 中设置 LLM_MODEL_ID 即可切换模型，例如：
#   qwen3.6-plus / qwen3.6-plus-2026-04-02 / qwen-max / qwen-turbo 等
# 使用LangChain兼容的格式https://bailian.console.aliyun.com/cn-beijing?spm=a2ty02.30260213.overview_recent.1.44b774a1K2ef8N&tab=api#/api/?type=model&url=2587654
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID", ),
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.7
)

# 备选：ChatTongyi 适配器（只支持 qwen-plus/qwen-max/qwen-turbo 等老代号，
# 无法指定模型广场的精确版本）
# from langchain_community.chat_models.tongyi import ChatTongyi
# llm = ChatTongyi(
#     model="qwen-plus",
#     api_key=os.getenv("DASHSCOPE_API_KEY"),
#     temperature=0.7
# )
# 初始化Tavily客户端
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

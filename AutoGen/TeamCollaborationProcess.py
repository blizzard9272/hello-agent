"""
团队协作流程定义。

采用 RoundRobinGroupChat（轮询群聊）模式：
  产品经理 → 工程师 → 代码审查员 → 用户代理 → 循环
直到用户代理输出 TERMINATE 或达到最大轮数。
"""

from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent


def create_team(
    product_manager: AssistantAgent,
    engineer: AssistantAgent,
    code_reviewer: AssistantAgent,
    user_proxy: UserProxyAgent,
    max_turns: int = 20,              # 默认的最大轮数为20
) -> RoundRobinGroupChat:
    """创建软件开发团队，返回配置好的群聊实例 RoundRobinGroupChat"""
    return RoundRobinGroupChat(
        participants=[
            product_manager, 
            engineer, 
            code_reviewer, 
            user_proxy
        ],
        termination_condition=TextMentionTermination("TERMINATE"),
        max_turns=max_turns,
    )

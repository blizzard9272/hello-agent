"""
程序主入口 —— 初始化模型客户端、创建 Agent、组建团队、启动协作任务。
并将智能体生成的代码/文档自动保存到 result/<timestamp>/ 目录。
"""

import asyncio
import sys, os
from autogen_agentchat.ui import Console

from ModeClient import create_model_client
from AgentRoles import (
    create_product_manager,
    create_engineer,
    create_code_reviewer,
    create_user_proxy,
)
from TeamCollaborationProcess import create_team
from FileExporter import FileExporter


async def run_software_development_team():
    """初始化团队并启动协作流程"""

    # 1. 创建模型客户端（可按需切换 provider）
    model_client = create_model_client("deepseek")

    # 2. 初始化各角色 Agent
    product_manager = create_product_manager(model_client)
    engineer        = create_engineer(model_client)
    code_reviewer   = create_code_reviewer(model_client)
    user_proxy      = create_user_proxy()

    # 3. 组建团队
    team = create_team(product_manager, engineer, code_reviewer, user_proxy)

    # 4. 定义任务
    task = """我们需要开发一个比特币价格显示应用，具体要求如下：
核心功能：
- 实时显示比特币当前价格（USD）
- 显示24小时价格变化趋势（涨跌幅和涨跌额）
- 提供价格刷新功能

技术要求：
- 使用 Streamlit 框架创建 Web 应用
- 界面简洁美观，用户友好
- 添加适当的错误处理和加载状态

请团队协作完成这个任务，从需求分析到最终实现。"""

    # 5. 初始化文件导出器
    exporter = FileExporter(base_dir="../result")
    print(f"\n{'='*60}")
    print(f"  输出目录：{exporter.session_dir}")
    print(f"{'='*60}\n")

    # 6. 流式执行协作（同时打印到控制台 + 写入文件）
    stream = team.run_stream(task=task)
    async for message in stream:
        # 写入导出器
        exporter.write_message(message)
        # 同时打印到控制台
        if hasattr(message, "source") and hasattr(message, "content"):
            print(f"\n--- [{message.source}] ---")
            print(message.content)

    # 7. 保存所有文件
    saved_dir = exporter.save_all()
    print(f"\n{'='*60}")
    print(f"  全部文件已保存至：{os.path.abspath(saved_dir)}")
    print(f"    conversation.md  — 完整对话记录")
    print(f"    code/            — 提取的代码文件")
    print(f"    agents/          — 各智能体独立输出")
    print(f"{'='*60}")

    return saved_dir


if __name__ == "__main__":
    asyncio.run(run_software_development_team())

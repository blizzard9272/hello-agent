from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from search_state import SearchState
from search_nodes import understand_query_node, tavily_search_node, generate_answer_node


def create_search_assistant():
    """创建并编译搜索助手工作流"""
    workflow = StateGraph(SearchState)

    # 添加节点
    workflow.add_node("understand", understand_query_node)
    workflow.add_node("search", tavily_search_node)
    workflow.add_node("answer", generate_answer_node)

    # 设置线性流程
    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", END)

    # 编译图
    memory = InMemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app


def main():
    """主函数：控制台交互式搜索助手"""
    print("=" * 60)
    print("🔍 智能搜索助手启动！")
    print("我会使用Tavily API为您搜索最新、最准确的信息")
    print("支持各种问题：新闻、技术、知识问答等")
    print("(输入 'quit' 退出)")
    print("=" * 60)

    # 创建搜索助手
    app = create_search_assistant()

    while True:
        try:
            print()
            user_input = input("🤔 您想了解什么: ").strip()

            if user_input.lower() == "quit":
                print("👋 感谢使用智能搜索助手，再见！")
                break

            if not user_input:
                print("⚠️  请输入您的问题。")
                continue

            # 配置（thread_id 用于记忆/检查点）
            config = {"configurable": {"thread_id": "search_session"}}

            # 初始状态
            initial_state = {
                "messages": [HumanMessage(content=user_input)]
            }

            print("\n⏳ 正在处理您的问题...\n")

            # 运行工作流
            final_state = app.invoke(initial_state, config)

            # 输出最终答案
            print("📋 " + "=" * 56)
            if final_state.get("final_answer"):
                print(final_state["final_answer"])
            else:
                # 如果工作流没有生成 final_answer，回退到最后一条 AI 消息
                messages = final_state.get("messages", [])
                ai_messages = [m for m in messages if m.type == "ai"]
                if ai_messages:
                    print(ai_messages[-1].content)
                else:
                    print("抱歉，未能获取到答案，请稍后再试。")
            print("=" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 检测到中断，感谢使用，再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            print("请重新输入您的问题。")


if __name__ == "__main__":
    main()

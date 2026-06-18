import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from init_config import llm, tavily_client
from search_state import SearchState


def understand_query_node(state: SearchState) -> dict:

    """步骤1：理解用户查询并生成搜索关键词"""

    user_message = state["messages"][-1].content
    
    understand_prompt = f"""分析用户的查询："{user_message}"
        请完成两个任务：
        1. 简洁总结用户想要了解什么
        2. 生成最适合搜索引擎的关键词（中英文均可，要精准）

        格式：
        理解：[用户需求总结]
        搜索词：[最佳搜索关键词]
    """

    response = llm.invoke([SystemMessage(content=understand_prompt)])
    response_text = response.content
    
    # 解析LLM的输出，提取搜索关键词
    search_query = user_message # 默认使用原始查询
    # 如果LLM输出中包含“搜索词：”，则提取后面的内容作为搜索关键词
    if "搜索词：" in response_text:
        search_query = response_text.split("搜索词：")[1].strip()
    
    return {
        "user_query": response_text,
        "search_query": search_query,
        "step": "understood",
        "messages": [AIMessage(content=f"我将为您搜索：{search_query}")]
    }

def tavily_search_node(state: SearchState) -> dict:

    """步骤2：使用Tavily API进行真实搜索"""

    search_query = state["search_query"]
    try:
        print(f"🔍 正在搜索: {search_query}")
        response = tavily_client.search(
            query=search_query,      # query就是调用查询的关键词
            search_depth="basic",    # 有四个选择：fast、ultra-fast、basic、advanced,分别对应不同的搜索深度和结果质量,越深质量越好但响应时间越长
            max_results=5,           # 返回的最大结果数
            include_answer=True      # 是否包含关键词查询的AI摘要答案（如果有的话），basic或True快速返回结果，advanced返回更详细的结果
        )

        # 格式化搜索结果
        formatted_results = ""
        
        # Tavily 的 AI 摘要答案
        if response.get("answer"):
            formatted_results += f"📝 AI摘要：{response['answer']}\n\n"

        # 搜索结果列表
        results = response.get("results", [])
        if results:
            formatted_results += "📚 相关搜索结果：\n"
            for i, result in enumerate(results, 1):
                title = result.get("title", "无标题")
                url = result.get("url", "")
                content = result.get("content", "无内容")
                formatted_results += f"\n{i}. {title}\n   URL: {url}\n   摘要: {content}\n"

        if not formatted_results:
            formatted_results = "未找到相关搜索结果。"

        return {
            "search_results": formatted_results,
            "step": "searched",
            "messages": [AIMessage(content="✅ 搜索完成！正在整理答案...")]
        }
    except Exception as e:
        print(f"❌ 搜索出错: {e}")
        return {
            "search_results": f"搜索失败：{e}",
            "step": "search_failed",
            "messages": [AIMessage(content=f"❌ 搜索遇到问题: {e}")]
        }

def generate_answer_node(state: SearchState) -> dict:

    """步骤3：基于搜索结果生成最终答案"""

    if state["step"] == "search_failed":
        # 如果搜索失败，执行回退策略，基于LLM自身知识回答
        fallback_prompt = f"搜索API暂时不可用，请基于您的知识回答用户的问题：\n用户问题：{state['user_query']}"
        response = llm.invoke([SystemMessage(content=fallback_prompt)])
    else:
        # 搜索成功，基于搜索结果生成答案
        answer_prompt = f"""基于以下搜索结果为用户提供完整、准确的答案：
            用户问题：{state['user_query']}
            搜索结果：\n{state['search_results']}
            请综合搜索结果，提供准确、有用的回答...
        """
        response = llm.invoke([SystemMessage(content=answer_prompt)])
    
    return {
        "final_answer": response.content,
        "step": "completed",
        "messages": [AIMessage(content=response.content)]
    }

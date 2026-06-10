"""
通过注册表 + 工厂函数管理多个模型厂商。

核心区别：
  - OpenAI 模型：AutoGen 原生支持，无需 model_info
  - 非 OpenAI 模型（DeepSeek 等）：必须提供 model_info 声明模型能力
"""

import os
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# 非 OpenAI 模型能力声明表
# OpenAI 模型（gpt-4o / gpt-3.5-turbo 等）AutoGen 原生支持，不需要在这里声明。
# 其他厂商的模型必须在此处填写 model_info，否则功能可能异常。
# =============================================================================
NON_OPENAI_MODEL_INFO: dict[str, dict] = {
    "deepseek-chat": {
        "function_calling": True,
        "max_tokens": 4096,
        "context_length": 32768,
        "vision": False,
        "json_output": True,
        "family": "deepseek",
        "structured_output": True,
    },
    # 未来新增模型在这里追加，例如：
    # "glm-4": { ... },
    # "moonshot-v1-8k": { ... },
}


# =============================================================================
# 厂商配置注册表
# "needs_model_info" 字段标记该厂商是否为非 OpenAI 规范模型，
# 为 True 时，必须在 NON_OPENAI_MODEL_INFO 中为该厂商的模型提供能力声明。
# =============================================================================
PROVIDER_CONFIGS: dict[str, dict] = {
    "openai": {
        "needs_model_info": False,                    # ← OpenAI 原生支持
        "env_key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
    },
    "deepseek": {
        "needs_model_info": True,                     # ← 非 OpenAI 模型，需 model_info
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
}

# OpenAI 原生支持的模型列表（可补充）
OPENAI_NATIVE_MODELS = {"gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "o1", "o1-mini", "o3-mini"}


# =============================================================================
# 工厂函数
# =============================================================================
def create_model_client(
    provider: str = "openai",
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAIChatCompletionClient:
    """
    统一的模型客户端工厂。

    根据厂商的 needs_model_info 标记决定是否传入 model_info：
      - OpenAI 厂商 → 不传 model_info（AutoGen 原生支持）
      - 其他厂商    → 必须传 model_info（否则 function calling / json_output 等能力不可用）
    """
    config = PROVIDER_CONFIGS[provider]

    model    = model or config["default_model"]
    api_key  = api_key or os.getenv(config["env_key"])
    base_url = base_url or config["base_url"]

    if not api_key:
        raise ValueError(
            f"未找到 {provider} 的 API Key，请设置环境变量 {config['env_key']} 或在代码中传入"
        )

    # ---- 关键分支：是否需要 model_info ----
    if config["needs_model_info"]:
        # 从非OpenAI模型信息表中获取模型能力信息
        model_info = NON_OPENAI_MODEL_INFO.get(model)
        if model_info is None:
            raise ValueError(
                f"模型 '{model}' 未在 NON_OPENAI_MODEL_INFO 中声明能力信息，"
                f"请补充后重试。"
            )
    else:
        # OpenAI 原生模型：不传 model_info，让 AutoGen 自行处理
        model_info = None

    return OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        model_info=model_info,
    )


# =============================================================================
# 便捷封装
# =============================================================================
def create_openai_model_client(model: str = "gpt-4o"):
    """OpenAI 客户端 —— 无需 model_info"""
    return create_model_client("openai", model=model)


def create_deepseek_model_client(model: str = "deepseek-chat"):
    """DeepSeek 客户端 —— 自动注入 model_info"""
    return create_model_client("deepseek", model=model)
from pydantic import BaseModel, Field
from typing import Optional

class DiscussionModelCN(BaseModel):
    """黑夜/白天讨论阶段的 AI 输出格式"""
    reach_agreement: bool = Field(
        default=False, 
        description="是否已与同伴达成一致意见"
    )

    confidence_level: int = Field(
        default=5, 
        ge=1, le=10, 
        description="对当前推理的信心程度(1-10)"
    )

    thought: str = Field(
        description="你的内心思考与局势分析"
    )

    suggested_target: Optional[str] = Field(
        default=None, 
        description="你建议或倾向的目标玩家姓名"
    )

class VoteModelCN(BaseModel):
    """最终投票阶段的 AI 输出格式"""
    target_name: str = Field(description="你决定投票杀死或投死的玩家绝对姓名")
    reason: str = Field(description="你投票给他的核心理由，会公开给大家")

class WitchActionModelCN(BaseModel):
    """女巫行动的输出格式"""
    use_antidote: bool = Field(description="是否使用解药")
    use_poison: bool = Field(description="是否使用毒药")
    target_name: Optional[str] = Field(description="毒药目标玩家姓名")

class SeerActionModelCN(BaseModel):
    """预言家行动的输出格式"""
    target_name: str = Field(description="你选择查验的玩家绝对姓名")
"""亲密语言策略，控制回复里的关系分寸。"""

from typing import Any

FORBIDDEN_PHRASES = {
    "只有我懂你": "会有人愿意认真听你说的",
    "你只需要我": "你也可以找身边可信的人一起撑一下",
    "别告诉别人": "这件事可以告诉可信的人",
    "离不开我也没关系": "你不用一个人扛着",
}
STRANGER_REPLACEMENTS = {
    "抱抱你": "先陪你一会儿",
    "我一直都在": "我现在在这儿",
    "靠着我": "先缓一缓",
}


def adjust_intimacy_language(text: str, relationship_state: Any) -> str:
    """根据关系阶段调整亲密表达，并移除依赖性表达。"""
    adjusted = text
    for phrase, replacement in FORBIDDEN_PHRASES.items():
        adjusted = adjusted.replace(phrase, replacement)

    stage = getattr(relationship_state, "relationship_stage", "stranger")
    if stage == "stranger":
        for phrase, replacement in STRANGER_REPLACEMENTS.items():
            adjusted = adjusted.replace(phrase, replacement)
    elif stage == "familiar":
        adjusted = adjusted.replace("靠着我", "先靠一会儿也行")
    elif stage in ["trusted", "close_friend"]:
        # 熟悉关系可以保留“我在”“慢慢来”，但前面的禁用依赖表达仍然生效。
        return adjusted

    return adjusted

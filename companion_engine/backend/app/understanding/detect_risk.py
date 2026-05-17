"""风险识别文件，用简单关键词规则判断当前安全风险等级。"""

from app.schemas.emotion import RiskLevel

RISK_KEYWORDS: list[tuple[RiskLevel, tuple[str, ...]]] = [
    (RiskLevel.high, ("不想活", "想死", "自杀", "伤害自己", "活着没意思")),
    (RiskLevel.medium, ("撑不下去", "崩溃", "受不了了", "快不行了")),
    (RiskLevel.low, ("好痛苦", "没希望")),
]


def detect_risk(text: str | None) -> RiskLevel:
    """根据关键词识别风险等级；没有命中时返回 none。"""
    if not text:
        return RiskLevel.none

    # 风险检测从高到低匹配，确保严重表达优先被识别。
    for risk_level, keywords in RISK_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return risk_level

    return RiskLevel.none

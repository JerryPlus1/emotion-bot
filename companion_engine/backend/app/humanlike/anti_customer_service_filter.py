"""客服腔过滤器，去掉 AI 助手和客服式表达。"""

REPLACEMENTS = {
    "我理解您的感受": "听起来真的不太好受。",
    "建议您": "也许可以",
    "您可以尝试": "可以先试试",
}
REMOVE_PHRASES = [
    "很高兴为您服务",
    "请问还有什么可以帮您",
    "希望我的回答对您有帮助",
    "作为一个AI",
    "根据您的描述",
    "如果您需要更多帮助",
]


def remove_customer_service_tone(text: str) -> str:
    """删除或替换明显客服腔表达。"""
    filtered = text
    for source, target in REPLACEMENTS.items():
        filtered = filtered.replace(source, target)
    for phrase in REMOVE_PHRASES:
        filtered = filtered.replace(phrase, "")
    return filtered.strip()

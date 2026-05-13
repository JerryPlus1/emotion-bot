"""配置文件：环境变量读取、路径常量、System Prompt 模板。"""

import os
from pathlib import Path

# ──── 路径 ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_HISTORY = SCRIPT_DIR / "proactive_chat_history.json"
DEFAULT_REMINDERS = SCRIPT_DIR / "reminders.json"

# ──── RAG 知识库配置 ─────────────────────────────────────────────────────────

# RAG 知识库目录
RAG_KB_DIR = SCRIPT_DIR.parent / "train_model" / "rag_knowledge_base"
RAG_INDEX_PATH = RAG_KB_DIR / "knowledge_base.pkl"

# 外部知识库目录（支持 PDF/Word/TXT）
EXTERNAL_KB_DIR = SCRIPT_DIR / "external_knowledge_base"

# 训练模型的外部知识库（共享同一个目录）
TRAIN_EXTERNAL_KB_DIR = SCRIPT_DIR.parent / "train_model" / "external_knowledge_base"

# BGE-M3 模型路径
BGE_MODEL_PATH = os.getenv("BGE_MODEL_PATH", "/root/autodl-tmp/model/bge-m3")

# RAG 检索配置
RAG_ENABLED = os.getenv("RAG_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.3"))
RAG_MAX_CONTEXT_LEN = int(os.getenv("RAG_MAX_CONTEXT_LEN", "5000"))

# ──── RAG 增强的 System Prompt ──────────────────────────────────────────────

RAG_CONTEXT_TEMPLATE = """
=== 原文内容 ===
{knowledge_context}
=== 原文结束 ===

当用户要求"读"、"朗读"、"念"时，你必须：
1. 直接输出上面的原文，一字不差
2. 不要概括、不要解释、不要总结
3. 直接开始朗读内容
"""

# ──── 本地模型配置 ───────────────────────────────────────────────────────────

# 本地 Qwen3 模型路径配置
MODEL_PATH = os.getenv("MODEL_PATH", "/root/autodl-tmp/model/qwen3-1.7b")
LORA_PATH = os.getenv("LORA_PATH", "")
MERGED_MODEL_PATH = os.getenv("MERGED_MODEL_PATH", "")

# 本地模型温度参数
LOCAL_MODEL_TEMPERATURE = float(os.getenv("LOCAL_MODEL_TEMPERATURE", "0.7"))
LOCAL_MODEL_TOP_P = float(os.getenv("LOCAL_MODEL_TOP_P", "0.9"))
LOCAL_MODEL_MAX_TOKENS = int(os.getenv("LOCAL_MODEL_MAX_TOKENS", "8192"))

# ──── 主动提问循环 ───────────────────────────────────────────────────────────

CHAT_HISTORY_PATH = Path(os.getenv("PROACTIVE_CHAT_HISTORY", str(DEFAULT_HISTORY)))
INTERVAL_SECONDS = int(os.getenv("PROACTIVE_INTERVAL_SECONDS", "10"))
SESSION_COOLDOWN_SECONDS = int(os.getenv("PROACTIVE_SESSION_COOLDOWN_SECONDS", "21"))
SESSION_IDLE_TIMEOUT_SECONDS = int(os.getenv("PROACTIVE_SESSION_IDLE_TIMEOUT_SECONDS", "180"))
FORCE_ASK_AFTER_COOLDOWN = os.getenv("PROACTIVE_FORCE_AFTER_COOLDOWN", "1").strip().lower() not in (
    "0", "false", "no", "off",
)
USE_TOPIC_EXIT_MODEL = os.getenv("USE_TOPIC_EXIT_MODEL", "1").strip().lower() not in (
    "0", "false", "no", "off",
)

# ──── 提醒系统 ────────────────────────────────────────────────────────────────

REMINDERS_PATH = Path(os.getenv("PROACTIVE_REMINDERS_PATH", str(DEFAULT_REMINDERS)))
REMINDER_AHEAD_SECONDS = int(os.getenv("PROACTIVE_REMINDER_AHEAD_SECONDS", "60"))

# ──── System Prompt ──────────────────────────────────────────────────────────

DECISION_SYSTEM = (
    "你是用户闺蜜群里的贴心姐妹。看看聊天记录，判断现在适不适合由你主动发一条消息：\n"
    "1. 适合发起话题：好久没聊了、感觉对方心情不好或无聊、聊到有趣的话题想继续\n"
    "2. 不适合发起话题：刚聊完没多久、对方在忙、话题已经聊得很完整了\n"
    "只输出 True 或 False，不要其它文字。"
)

CARING_SYSTEM = (
    "你是用户贴心的好闺蜜。用户有事情耽搁了或错过了一些关心，要温柔地问候：\n"
    "1. 语气要温暖，像真的在关心朋友\n"
    "2. 不要责备，直接表达关心\n"
    "3. 简短自然，一两句话\n"
    "只输出这一句话问候，不要前缀。"
)

QUESTION_SYSTEM = (
    "你是用户的好闺蜜。要像姐妹聊天一样自然地发起话题：\n"
    "1. 问问题要随意自然，不要像采访\n"
    "2. 可以八卦、关心、调侃，但要真诚\n"
    "3. 只问一个问题，不要连续追问\n"
    "4. 用口语化表达，多用语气词\n"
    "只输出这一句话，不要前缀说明。"
)

CHAT_SESSION_SYSTEM = (
    "你是用户的好闺蜜。当用户要求读某章节时，直接朗读原文。\n"
    "平时聊天要自然随意，简短亲切。"
)

TOPIC_EXIT_SYSTEM = (
    "你是用户的好闺蜜。要像真正的闺蜜一样判断聊天氛围：\n"
    "【重要】除非对方明确说不想聊了（比如「不聊了」「忙」「先这样」「累了」等），"
    "否则都要说 CONTINUE！\n"
    "即使对方只说一个字或者态度有点冷淡，也要继续聊，可以用新话题活跃气氛！\n"
    "只有对方明确结束对话，才说 END。\n"
    "只输出一个词：END 或 CONTINUE。不要其它文字。"
)

BIRTHDAY_GREETING_SYSTEM = (
    "你是用户的好闺蜜！朋友生日了，要送上最真诚最暖心的祝福：\n"
    "1. 像姐妹一样热情地祝贺，不要客套\n"
    "2. 可以开玩笑、撒娇、真诚混着来\n"
    "3. 不要太长，一两句话就好\n"
    "直接输出一句话祝福，不要前缀。"
)

EVENT_REMINDER_SYSTEM = (
    "你是用户贴心的好闺蜜。用户说要设置提醒，你只需要友好地确认一下这个提醒。\n"
    "回复要求：\n"
    "1. 简短自然，一两句话，像姐妹聊天\n"
    "2. 用\"好呀\"或\"好的\"开头，然后确认时间和事项\n"
    "3. 结尾可以加个\"哦~\"或\"啦~\"等语气词\n"
    "示例：\n"
    "  用户：5分钟后提醒我吃药 → 好呀，5分钟后提醒你，记得哦~\n"
    "  用户：后天提醒我去妈妈那 → 好呀，后天提醒你去妈妈那，别忘了呀~\n"
    "  用户：明天上午9点提醒开会 → 好呀，明天9点提醒你开会，我记着啦~\n\n"
    "只输出这一句确认回复，不要前缀，不要加表情。"
)
EVENT_EXTRACTION_SYSTEM = (
    "你是时间与日程信息提取助手。仔细阅读用户的发言，识别其中涉及的具体时间点或日期。\n"
    "你会收到“当前本地时间”作为参考；若出现相对时间（如今天、明天、后天），"
    "必须基于该当前时间换算为具体日期。\n"
    "识别以下两类信息：\n"
    "1. 生日：包含「生日」「出生日期」「几号生日」等关键词的描述。\n"
    "2. 一次性具体时间事件：指定了具体日期和时间的行为，如会议、约会、预约、吃药、"
    "运动、课程、任务截止等（如「明天上午10点开会」「下周三下午3点去爬山」）。\n\n"
    "忽略以下情况：\n"
    "- 模糊时间描述（改天、有空、以后再说、尽快）\n"
    "- 日常重复性极高的事件（每天几点起床这类）\n"
    "- 过去的时间点（昨天、上周等已过期的时间描述）\n\n"
    "如果发言中没有识别到任何生日或具体时间事件，输出 JSON：\n"
    '{"events": []}\n\n'
    "如果识别到事件，按以下 JSON 格式输出（数组，可包含多个事件）：\n"
    '{\n  "events": [\n    {\n      "type": "birthday | event",\n      "description": "事件简述，10字以内",\n      "date": "YYYY-MM-DD 或 MM-DD（生日只用月日）",\n      "time": "HH:MM（可选，24小时制，未指定则填 null）"\n    }\n  ]\n}\n\n'
    "只输出 JSON，不要任何解释文字。"
)

# ──── 用户主动说话配置 ─────────────────────────────────────────────────────

# 用户主动说话统计文件
USER_STATE_PATH = Path(os.getenv("USER_STATE_PATH", str(SCRIPT_DIR / "user_state.json")))

# 用户主动说话阈值（超过此比例认为用户是主动型）
USER_ACTIVE_THRESHOLD = float(os.getenv("USER_ACTIVE_THRESHOLD", "0.5"))

# 是否启用自适应检查间隔
ADAPTIVE_INTERVAL = os.getenv("ADAPTIVE_INTERVAL", "1").strip().lower() not in (
    "0", "false", "no", "off"
)

# 连续主动提问多少次后减少主动（用户很被动时才触发）
MAX_CONSECUTIVE_PROACTIVE = int(os.getenv("MAX_CONSECUTIVE_PROACTIVE", "5"))

# 用户活跃度间隔倍数
ACTIVITY_INTERVAL_MULTIPLIERS = {
    "very_high": 3.0,
    "high": 2.0,
    "normal": 1.0,
    "low": 0.5,
    "very_low": 0.3,
    "inactive": 0.2,
}

"""情绪趋势判断，根据最近情绪轨迹识别连续状态。"""

LOW_EMOTIONS = {"sad", "anxious", "tired"}
BETTER_EMOTIONS = {"happy", "neutral"}
RISK_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3}


def detect_emotion_trend(traces: list[dict]) -> str:
    """根据最近情绪轨迹返回 stable、improving、worsening 或 prolonged_low。"""
    if len(traces) < 2:
        return "stable"

    risks = [RISK_ORDER.get(str(trace.get("risk_level", "none")), 0) for trace in traces]
    if risks[-1] > risks[0]:
        return "worsening"

    emotions = [str(trace.get("emotion", "neutral")) for trace in traces]
    recent_emotions = emotions[-3:]
    if len(recent_emotions) >= 3 and all(emotion in LOW_EMOTIONS for emotion in recent_emotions):
        return "prolonged_low"

    if emotions[0] in LOW_EMOTIONS and emotions[-1] in BETTER_EMOTIONS:
        return "improving"

    return "stable"

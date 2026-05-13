"""输入处理器。

处理用户输入和事件提取。
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class InputHandler:
    """输入处理器"""

    def __init__(self):
        self._init_patterns()

    def _init_patterns(self):
        """初始化匹配模式"""
        # 事件提取正则
        self.event_patterns = [
            # 生日
            (r'(.+?)生日', 'birthday'),
            (r'出生日期[是为]*(\d{1,2}[-/]\d{1,2})', 'birthday'),
            # 会议
            (r'(\d{1,2}[-:]\d{2})\s*(?:开会|会议|会)', 'meeting'),
            (r'明天\s*(\d{1,2}[-:]\d{2})\s*(?:开会|会议)', 'meeting'),
            # 提醒
            (r'(\d+)\s*(?:分钟|min|小时后?)\s*(?:提醒我|叫我|提醒)', 'timer'),
            (r'明天\s*(.+?)\s*(?:提醒|叫我)', 'reminder'),
            (r'(.+?)\s*(?:几点|什么时候)', 'query_time'),
        ]

    def extract_events(self, text: str) -> List[Dict[str, Any]]:
        """提取事件"""
        events = []

        # 生日
        birthday_matches = re.findall(r'(.+?)生日', text)
        for match in birthday_matches:
            events.append({
                "type": "birthday",
                "description": match.strip(),
                "date": self._parse_date_from_text(text),
                "time": None,
            })

        # 定时提醒
        timer_matches = re.findall(r'(\d+)\s*(?:分钟|min|小时后?)', text)
        for match in timer_matches:
            events.append({
                "type": "timer",
                "description": self._extract_timer_description(text),
                "duration_minutes": int(match),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": None,
            })

        return events

    def _parse_date_from_text(self, text: str) -> Optional[str]:
        """从文本解析日期"""
        now = datetime.now()

        # 今天
        if '今天' in text:
            return now.strftime("%Y-%m-%d")

        # 明天
        if '明天' in text:
            tomorrow = now.replace(day=now.day + 1)
            return tomorrow.strftime("%Y-%m-%d")

        # 具体日期
        date_match = re.search(r'(\d{1,2})[/\-月](\d{1,2})', text)
        if date_match:
            month, day = int(date_match.group(1)), int(date_match.group(2))
            return f"{now.year}-{month:02d}-{day:02d}"

        return None

    def _extract_timer_description(self, text: str) -> str:
        """提取定时描述"""
        # 移除时间部分
        text = re.sub(r'\d+\s*(?:分钟|min|小时后?)', '', text)
        # 移除常见前缀
        text = re.sub(r'^(?:提醒我|叫我|记得|别忘了)', '', text)
        return text.strip() or "定时提醒"

    def is_end_keyword(self, text: str) -> bool:
        """判断是否为结束关键词"""
        end_keywords = {
            '结束', '拜拜', '回见', '再见', '不聊了', '不说了',
            '不想聊了', '先这样', '就这样吧', '先挂了',
            '不想说了', '不想聊了', '不想继续', '先忙了',
            '不想谈了', '不打扰了', '没空', '先走了',
        }

        text_lower = text.lower()
        for keyword in end_keywords:
            if keyword in text:
                return True

        return False

    def is_read_request(self, text: str) -> bool:
        """判断是否为朗读请求"""
        read_keywords = ['读', '朗读', '念', '念一下', '读一下', '读读']
        return any(kw in text for kw in read_keywords)

    def extract_read_request(self, text: str) -> Optional[Dict[str, Any]]:
        """提取朗读请求信息"""
        if not self.is_read_request(text):
            return None

        result = {
            "book": None,
            "chapter": None,
            "chapter_type": None,  # 回、章、篇
        }

        # 书籍识别
        books = ['红楼梦', '石头记', '金瓶梅', '西游记', '水浒传', '三国演义']
        for book in books:
            if book in text:
                result["book"] = book
                break

        # 章节提取
        patterns = [
            (r'第([一二三四五六七八九十百千万\d]+)[回章节篇]', 'full'),
            (r'第(\d+)\s*[回章节篇]', 'number'),
        ]

        for pattern, match_type in patterns:
            match = re.search(pattern, text)
            if match:
                result["chapter"] = match.group(1)
                result["chapter_type"] = self._detect_chapter_type(text)
                break

        return result if result["book"] or result["chapter"] else None

    def _detect_chapter_type(self, text: str) -> str:
        """检测章节类型"""
        if '回' in text:
            return '回'
        if '章' in text:
            return '章'
        if '篇' in text:
            return '篇'
        return '回'  # 默认

    def sanitize_input(self, text: str) -> str:
        """清理输入"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除控制字符
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        return text.strip()

    def is_empty_input(self, text: str) -> bool:
        """判断是否为空输入"""
        return not text or not text.strip()

    def get_intent(self, text: str) -> str:
        """获取用户意图"""
        text = text.strip()

        # 结束
        if self.is_end_keyword(text):
            return "end"

        # 朗读
        if self.is_read_request(text):
            return "read"

        # 提取事件
        events = self.extract_events(text)
        if events:
            return "schedule"

        # 问候
        greeting_keywords = ['你好', '嗨', 'hi', 'hello', '早上好', '晚安']
        for kw in greeting_keywords:
            if kw in text.lower():
                return "greeting"

        # 默认
        return "chat"


def get_input_handler() -> InputHandler:
    """获取输入处理器"""
    return InputHandler()

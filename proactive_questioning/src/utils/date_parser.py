"""日期解析工具。"""

import re
from datetime import datetime, timedelta, date
from typing import Optional, Tuple


class DateParser:
    """日期解析器"""

    @staticmethod
    def parse_relative(text: str, reference: Optional[datetime] = None) -> Optional[date]:
        """解析相对日期"""
        if reference is None:
            reference = datetime.now()

        today = reference.date()

        # 今天
        if '今天' in text:
            return today

        # 明天
        if '明天' in text:
            return today + timedelta(days=1)

        # 后天
        if '后天' in text:
            return today + timedelta(days=2)

        # 前天
        if '前天' in text:
            return today - timedelta(days=2)

        # 昨天
        if '昨天' in text:
            return today - timedelta(days=1)

        # 下周
        week_match = re.search(r'下周[一二三四五六日天]', text)
        if week_match:
            days_ahead = 7 - today.weekday() + ['一', '二', '三', '四', '五', '六', '日'].index(week_match.group(0)[-1])
            return today + timedelta(days=days_ahead)

        # 本周
        week_match = re.search(r'本周[一二三四五六日天]', text)
        if week_match:
            days_ahead = ['一', '二', '三', '四', '五', '六', '日'].index(week_match.group(0)[-1]) - today.weekday()
            if days_ahead < 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)

        # 几天后
        days_match = re.search(r'(\d+)\s*(?:天|日)后', text)
        if days_match:
            days = int(days_match.group(1))
            return today + timedelta(days=days)

        return None

    @staticmethod
    def parse_absolute(text: str, reference: Optional[datetime] = None) -> Optional[date]:
        """解析绝对日期"""
        if reference is None:
            reference = datetime.now()

        # YYYY-MM-DD
        match = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})', text)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                return date(year, month, day)
            except ValueError:
                pass

        # MM-DD
        match = re.search(r'(\d{1,2})[-/月](\d{1,2})', text)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            try:
                return date(reference.year, month, day)
            except ValueError:
                pass

        return None

    @staticmethod
    def parse_time(text: str) -> Optional[str]:
        """解析时间"""
        # HH:MM
        match = re.search(r'(\d{1,2}):(\d{2})', text)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"

        # 几点
        hour_match = re.search(r'(\d+)\s*(?:点|点钟)', text)
        minute_match = re.search(r'([一二三四五六七八九十零]+)?\s*(?:分|分钟)?', text)
        if hour_match:
            hour = int(hour_match.group(1))
            minute = 0
            if minute_match and minute_match.group(1):
                minute = ChineseToNumber.parse(minute_match.group(1))
            return f"{hour:02d}:{minute:02d}"

        return None

    @staticmethod
    def parse(text: str, reference: Optional[datetime] = None) -> Tuple[Optional[date], Optional[str]]:
        """解析日期和时间"""
        parsed_date = DateParser.parse_relative(text, reference)
        if not parsed_date:
            parsed_date = DateParser.parse_absolute(text, reference)

        parsed_time = DateParser.parse_time(text)

        return parsed_date, parsed_time


# 简化中文数字解析
class ChineseToNumber:
    """中文数字转阿拉伯数字"""

    _map = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    }

    @classmethod
    def parse(cls, s: str) -> int:
        if s.isdigit():
            return int(s)

        result = 0
        temp = 0
        for char in s:
            if char in cls._map:
                val = cls._map[char]
                if val >= 10:
                    result = (result + temp) * val
                    temp = 0
                else:
                    temp += val
        return result + temp

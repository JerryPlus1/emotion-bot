"""文本处理工具。"""

import re
from typing import Optional


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """清理文本"""
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 移除控制字符
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    # 移除首尾空白
    text = text.strip()
    return text


def extract_keywords(text: str, max_count: int = 5) -> list:
    """提取关键词"""
    # 简单实现：提取连续的中文/英文词组
    keywords = []

    # 中文词组
    cn_pattern = re.compile(r'[\u4e00-\u9fa5]{2,}')
    cn_matches = cn_pattern.findall(text)
    keywords.extend(cn_matches[:max_count])

    # 英文词
    en_pattern = re.compile(r'[a-zA-Z]{3,}')
    en_matches = en_pattern.findall(text)
    keywords.extend(en_matches[:max_count])

    return keywords[:max_count]


def mask_sensitive_info(text: str) -> str:
    """脱敏处理"""
    # 手机号
    text = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', text)
    # 邮箱
    text = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                  lambda m: m.group(1)[:2] + '***@' + m.group(2), text)
    return text


def count_chinese_chars(text: str) -> int:
    """统计中文字符数"""
    return len(re.findall(r'[\u4e00-\u9fa5]', text))


def count_words(text: str) -> int:
    """统计词数（中文按字，英文按词）"""
    cn_count = count_chinese_chars(text)
    en_pattern = re.compile(r'[a-zA-Z]+')
    en_count = len(en_pattern.findall(text))
    return cn_count + en_count

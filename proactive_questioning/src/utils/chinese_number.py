"""中文数字解析工具。"""


class ChineseNumberParser:
    """中文数字解析器"""

    _cn_nums = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '百': 100, '千': 1000, '万': 10000,
    }

    @classmethod
    def parse(cls, s: str) -> int:
        """解析中文数字为整数"""
        if not s:
            return 0

        # 纯数字
        if s.isdigit():
            return int(s)

        # 中文数字
        result = 0
        temp = 0

        for char in s:
            if char in cls._cn_nums:
                val = cls._cn_nums[char]
                if val >= 100:
                    # 百、千、万：result = (result + temp) * val
                    result = (result + temp) * val
                    temp = 0
                elif val == 10:
                    # 十
                    if temp > 0:
                        result = result * 10 + temp * 10
                    else:
                        result = result * 10 if result else 10
                    temp = 0
                elif val > 0:
                    temp += val
            elif char.isdigit():
                temp = temp * 10 + int(char)

        return result + temp

    @classmethod
    def to_arabic(cls, cn_str: str) -> int:
        """中文数字转阿拉伯数字"""
        return cls.parse(cn_str)

    @classmethod
    def validate(cls, s: str) -> bool:
        """验证是否为有效的中文数字"""
        if s.isdigit():
            return True

        for char in s:
            if char not in cls._cn_nums and not char.isdigit():
                return False
        return True


def parse_chinese_number(s: str) -> int:
    """解析中文数字"""
    return ChineseNumberParser.parse(s)

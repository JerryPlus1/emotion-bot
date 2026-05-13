#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为知识库构建章节索引（改进版）

分析文本中的章节标记，保存每个章节的起始chunk位置。

用法:
    python build_chapter_index.py
"""

import json
import re
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
CHUNKS_PATH = SCRIPT_DIR / "rag_knowledge_base" / "knowledge_chunks.json"
INDEX_OUTPUT = SCRIPT_DIR / "rag_knowledge_base" / "chapter_index.json"


def extract_chapter_markers():
    """从 chunks 中提取章节标记"""
    print("加载 chunks...")
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    chunks = data.get("chunks", [])
    metadatas = data.get("metadatas", [])
    
    print(f"总 chunks: {len(chunks)}")
    
    # 中文数字映射
    cn_nums = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '百': 100, '千': 1000, '万': 10000,
    }
    
    def parse_chapter_num(num_str):
        """解析中文数字"""
        if num_str.isdigit():
            return int(num_str)
        result = 0
        temp = 0
        for char in num_str:
            if char in cn_nums:
                val = cn_nums[char]
                if char == '十':
                    if temp == 0:
                        result = 10
                    else:
                        result = result * 10 + val if result else val
                    temp = 0
                elif val >= 10:
                    result = result * val if result else val
                    temp = 0
                else:
                    temp += val
            elif char.isdigit():
                temp = temp * 10 + int(char) if temp else int(char)
        return result + temp
    
    # 章节标记正则
    chapter_pattern = r'第([一二三四五六七八九十百千万\d]+)回'
    chapter_end_pattern = r'要知后事如何.*?下回*分解'
    
    # 按书名分组章节
    book_chapters = defaultdict(list)
    
    print("分析章节标记...")
    current_book = None
    current_chapter = None
    
    for i, (chunk, meta) in enumerate(zip(chunks, metadatas)):
        source = meta.get('source', 'unknown')
        
        # 换书了
        if source != current_book:
            current_book = source
            current_chapter = None
        
        # 查找章节开始 - 只检查 chunk 开头（前150个字符）
        chunk_start = chunk[:150]
        matches = re.findall(chapter_pattern, chunk_start)
        for match in matches:
            try:
                chapter_num = parse_chapter_num(match)
                chapter_info = {
                    'chunk_idx': i,
                    'chapter': match,
                    'chapter_num': chapter_num,
                    'preview': chunk[:80].strip(),
                }
                book_chapters[source].append(chapter_info)
                current_chapter = chapter_info
            except:
                pass
        
        if (i + 1) % 50000 == 0:
            print(f"  进度: {i + 1}/{len(chunks)}")
    
    # 排序并去重（同章节号只保留第一个）
    for source in book_chapters:
        # 按 chunk_idx 排序
        sorted_chapters = sorted(book_chapters[source], key=lambda x: x['chunk_idx'])
        
        # 去重：同章节号只保留第一个
        seen = {}
        unique = []
        for ch in sorted_chapters:
            num = ch['chapter_num']
            if num not in seen:
                seen[num] = True
                unique.append(ch)
            # 如果同章节号但之前的预览太短（可能是误匹配），替换
            elif num in seen:
                prev = next((u for u in unique if u['chapter_num'] == num), None)
                if prev and len(prev['preview']) < 30 and len(ch['preview']) > len(prev['preview']):
                    unique = [u if u['chapter_num'] != num else ch for u in unique]
        
        book_chapters[source] = unique
    
    return book_chapters


def save_index(book_chapters):
    """保存索引"""
    # 转为普通 dict
    index_data = {k: v for k, v in book_chapters.items()}
    
    with open(INDEX_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n索引已保存: {INDEX_OUTPUT}")
    
    # 统计
    print(f"有章节标记的书籍: {len(book_chapters)}")
    for source, chapters in sorted(book_chapters.items(), key=lambda x: -len(x[1]))[:15]:
        print(f"  {source}: {len(chapters)} 章节")


def main():
    print("=" * 60)
    print("构建章节索引")
    print("=" * 60)
    
    book_chapters = extract_chapter_markers()
    save_index(book_chapters)
    
    # 显示红楼梦相关
    print("\n红楼梦相关:")
    for k, v in book_chapters.items():
        if '红' in k or 'hong' in k.lower():
            print(f"  {k}: {len(v)} 章节")
    
    print("=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量重命名文件，只保留书名"""

import os
import re

dir_path = "/root/autodl-tmp/SA/proactive_questioning/external_knowledge_base/literature-books-master/文学"

for filename in os.listdir(dir_path):
    if not filename.endswith('.txt'):
        continue
    
    filepath = os.path.join(dir_path, filename)
    if os.path.isdir(filepath):
        continue
    
    new_name = filename
    
    # 处理《书名》作者 格式 -> 书名.txt
    match = re.search(r'^《([^》]+)》', new_name)
    if match:
        new_name = match.group(1) + ".txt"
    
    # 去掉 [分类] 前缀
    new_name = re.sub(r'^\[[^\]]+\]', '', new_name)
    
    # 去掉 " - " 或 "——" 后的作者/版本信息
    for sep in [' - ', ' — ', '——', '－', '—', '-']:
        if sep in new_name and not new_name.startswith(sep):
            parts = new_name.split(sep)
            if len(parts) > 1 and len(parts[0]) > 2:
                new_name = parts[0]
                break
    
    # 去掉 "全集" "连载" "完结" "大字版" "扫描版" 等后缀
    new_name = re.sub(r'\s*(全集|连载|完结|Ⅰ+Ⅱ.*)$', '', new_name)
    
    # 去掉括号内容
    new_name = re.sub(r'\s*\([^\)]*\)\s*', '', new_name)
    new_name = re.sub(r'\s*（[^）]*）\s*', '', new_name)
    
    new_name = new_name.strip()
    
    if new_name != filename and new_name:
        new_path = os.path.join(dir_path, new_name)
        if os.path.exists(new_path):
            base, ext = os.path.splitext(new_name)
            i = 1
            while os.path.exists(new_path):
                new_name = f"{base}_{i}{ext}"
                new_path = os.path.join(dir_path, new_name)
                i += 1
        
        os.rename(filepath, new_path)
        print(f"✓ {filename} -> {new_name}")

print("\n完成!")

#!/usr/bin/env python3
"""继续清理文件名"""

import os
import re

def clean_filename(filename):
    name = filename
    
    # 修复之前脚本的遗留问题
    name = re.sub(r'金庸-侠客行txt\.txt$', '金庸-侠客行.txt', name)
    name = re.sub(r'24堂财富课-\.txt$', '24堂财富课.txt', name)
    name = re.sub(r'人生的枷锁_\.txt$', '人生的枷锁.txt', name)
    name = re.sub(r'txt\.txt$', '.txt', name)
    
    # 处理 (1) 等重复标记
    name = re.sub(r'\(1\)\.txt$', '.txt', name)
    
    return name

base_dir = "/root/autodl-tmp/SA/proactive_questioning/external_knowledge_base/literature-books-master"

changes = []
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if not f.endswith('.txt'):
            continue
        
        old_path = os.path.join(root, f)
        new_name = clean_filename(f)
        new_path = os.path.join(root, new_name)
        
        if old_path != new_path:
            if os.path.exists(new_path) and old_path != new_path:
                # 保留非(1)版本
                os.remove(old_path)
                changes.append(f"删除重复: {f}")
            else:
                os.rename(old_path, new_path)
                changes.append(f"重命名: {f} -> {new_name}")

print(f"处理了 {len(changes)} 个文件：")
for c in changes:
    print(f"  {c}")

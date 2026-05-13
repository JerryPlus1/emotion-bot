#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
构建完整向量索引 - 对所有文本构建向量
"""

import json
import pickle
import numpy as np
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModel

SCRIPT_DIR = Path(__file__).resolve().parent
CHUNKS_PATH = SCRIPT_DIR / "rag_knowledge_base" / "knowledge_chunks.json"
INDEX_OUTPUT = SCRIPT_DIR / "rag_knowledge_base" / "knowledge_base.pkl"
BGE_MODEL_PATH = "/root/autodl-tmp/model/bge-m3"


def encode_texts(texts, batch_size=32):
    """编码文本"""
    print("加载 BGE-M3 模型...")
    tokenizer = AutoTokenizer.from_pretrained(BGE_MODEL_PATH, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        BGE_MODEL_PATH, trust_remote_code=True, torch_dtype=torch.float16
    ).cuda()
    model.eval()
    
    all_embeddings = []
    total = len(texts)
    
    print(f"编码 {total} 个文本块...")
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch = texts[i: i + batch_size]
            inputs = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(model.device)
            
            outputs = model(**inputs)
            hidden = outputs.last_hidden_state
            
            mask = inputs["attention_mask"].unsqueeze(-1).expand(hidden.size()).float()
            sum_emb = torch.sum(hidden * mask, dim=1)
            sum_mask = torch.clamp(mask.sum(dim=1), min=1e-9)
            emb = sum_emb / sum_mask
            emb = emb / emb.norm(dim=-1, keepdim=True)
            
            all_embeddings.append(emb.cpu().float().numpy())
            
            if (i + batch_size) % 1000 == 0 or i + batch_size >= total:
                print(f"  进度: {min(i + batch_size, total)}/{total} ({(i+batch_size)/total*100:.1f}%)")
    
    return np.concatenate(all_embeddings, axis=0)


def main():
    print("=" * 60)
    print("构建完整向量索引")
    print("=" * 60)
    
    # 加载 chunks
    print("\n[1] 加载 chunks...")
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    all_chunks = data.get("chunks", [])
    all_metas = data.get("metadatas", [])
    print(f"  总 chunk 数: {len(all_chunks)}")
    
    # 编码所有文本
    print("\n[2] 编码所有文本...")
    vectors = encode_texts(all_chunks, batch_size=32)
    print(f"  向量维度: {vectors.shape}")
    
    # 保存索引
    print("\n[3] 保存索引...")
    index_data = {
        "documents": all_chunks,
        "metadatas": all_metas,
        "vectors": vectors,
        "embedding_dim": 1024,
        "use_vector": True,
    }
    
    with open(INDEX_OUTPUT, "wb") as f:
        pickle.dump(index_data, f)
    
    print(f"\n索引已保存: {INDEX_OUTPUT}")
    print(f"  总文档: {len(all_chunks)}")
    print(f"  向量维度: {vectors.shape}")
    print("=" * 60)
    print("构建完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

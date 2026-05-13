#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG 检索工具模块

为 proactive_questioning 提供 RAG 知识检索能力。
使用 train_model 中的 BGE-M3 嵌入模型和向量检索。
支持章节快速定位。
"""

import os
import re
import sys
import pickle
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import numpy as np

# 尝试从 train_model 导入 RAG 模块
TRAIN_MODEL_DIR = Path(__file__).parent.parent / "train_model"
if TRAIN_MODEL_DIR.exists():
    sys.path.insert(0, str(TRAIN_MODEL_DIR))

# RAG 配置
TRAIN_MODEL_DIR = Path(__file__).parent.parent / "train_model"
RAG_KB_DIR = Path(__file__).parent / "rag_knowledge_base"
EXTERNAL_KB_DIR = Path(__file__).parent / "external_knowledge_base"
RAG_INDEX_PATH = RAG_KB_DIR / "knowledge_base.pkl"
CHAPTER_INDEX_PATH = RAG_KB_DIR / "chapter_index.json"
BGE_MODEL_PATH = "/root/autodl-tmp/model/bge-m3"


class SimpleRAGRetriever:
    """
    轻量级 RAG 检索器
    
    提供知识检索功能，检索结果可用于增强模型回复。
    """
    
    _instance: Optional["SimpleRAGRetriever"] = None
    
    def __init__(self):
        self.embedder = None
        self.vector_store = None
        self.documents: List[str] = []
        self.metadatas: List[Dict] = []
        self.vectors = None
        self.embedding_dim = 0
        self._initialized = False
        self.chapter_index: Dict[str, List] = {}
        
        # 延迟初始化
        self._init_components()
    
    @classmethod
    def get_instance(cls) -> "SimpleRAGRetriever":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _init_components(self):
        """初始化组件"""
        if self._initialized:
            return
        
        # 1. 加载 BGE-M3 模型
        self._init_embedder()
        
        # 2. 加载向量索引
        self._load_index()
        
        self._initialized = True
    
    def _init_embedder(self):
        """初始化嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            print("加载 BGE-M3 嵌入模型...")
            
            # 尝试本地模型
            model_path = BGE_MODEL_PATH
            if not os.path.exists(model_path):
                model_path = "BAAI/bge-m3"
                print(f"本地模型不存在，使用 HuggingFace: {model_path}")
            
            # 使用 sentence_transformers 加载，自动处理 safetensors
            self.model = SentenceTransformer(model_path, device='cuda')
            
            self.embedding_dim = self.model.get_embedding_dimension()
            print(f"BGE-M3 加载完成，嵌入维度: {self.embedding_dim}")
            
        except Exception as e:
            print(f"警告: BGE-M3 模型加载失败: {e}")
            print("将使用关键词匹配作为备选")
            self.model = None
    
    def _load_index(self):
        """加载向量索引"""
        if not RAG_INDEX_PATH.exists():
            print(f"警告: 知识库索引不存在: {RAG_INDEX_PATH}")
            print("请先运行 train_model 中的 RAG 索引构建")
            self._try_load_chunks()
            return
        
        try:
            with open(RAG_INDEX_PATH, "rb") as f:
                data = pickle.load(f)
            
            self.documents = data.get("documents", [])
            self.metadatas = data.get("metadatas", [])
            self.vectors = data.get("vectors")
            self.vector_doc_indices = data.get("vector_doc_indices", None)
            self.has_full_vector = data.get("has_full_vector", self.vectors is not None)
            
            if self.vectors is not None and self.vector_doc_indices:
                print(f"知识库加载完成: {len(self.documents)} 条知识 (部分向量: {len(self.vector_doc_indices)} 条)")
            else:
                print(f"知识库加载完成: {len(self.documents)} 条知识")
            
            # 加载章节索引
            self._load_chapter_index()
            
        except Exception as e:
            print(f"警告: 知识库加载失败: {e}")
            self._try_load_chunks()
    
    def _load_chapter_index(self):
        """加载章节索引"""
        if not CHAPTER_INDEX_PATH.exists():
            print("章节索引不存在，跳过")
            return
        
        try:
            with open(CHAPTER_INDEX_PATH, "r", encoding="utf-8") as f:
                self.chapter_index = json.load(f)
            print(f"章节索引加载完成: {len(self.chapter_index)} 本书有章节标记")
        except Exception as e:
            print(f"章节索引加载失败: {e}")
    
    def _try_load_chunks(self):
        """尝试加载 chunks JSON 文件"""
        chunks_path = RAG_KB_DIR / "knowledge_chunks.json"
        if chunks_path.exists():
            try:
                with open(chunks_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.documents = data.get("chunks", [])
                self.metadatas = data.get("metadatas", [])
                print(f"从 chunks 加载: {len(self.documents)} 条知识")
            except Exception as e:
                print(f"警告: chunks 加载失败: {e}")
    
    def _encode_text(self, text: str) -> np.ndarray:
        """编码文本为向量"""
        if self.model is None:
            return np.zeros(self.embedding_dim or 1024)
        
        # 使用 SentenceTransformer 编码
        embedding = self.model.encode([text], normalize_embeddings=True)[0]
        return embedding.astype(np.float32)
    
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.3,
    ) -> List[Dict]:
        """
        检索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回前 k 条
            min_score: 最小相似度分数
        
        Returns:
            检索结果列表，每项包含 content, metadata, score
        """
        if not self.documents:
            return []
        
        # 检查是否需要章节感知检索
        chapter_result = self._chapter_aware_retrieve(query, top_k)
        if chapter_result:
            return chapter_result
        
        # 编码查询
        query_vec = self._encode_text(query)
        
        # 计算相似度
        if self.vectors is not None:
            similarities = np.dot(self.vectors, query_vec)
            
            # 排序
            indices = np.argsort(similarities)[::-1]
            
            results = []
            for sim_idx in indices[:top_k * 3]:  # 取更多候选
                # 如果有 vector_doc_indices，需要映射回文档索引
                if self.vector_doc_indices is not None:
                    if sim_idx >= len(self.vector_doc_indices):
                        continue
                    doc_idx = self.vector_doc_indices[sim_idx]
                else:
                    doc_idx = sim_idx
                
                score = float(similarities[sim_idx])
                if score < min_score:
                    break
                results.append({
                    "content": self.documents[doc_idx],
                    "metadata": self.metadatas[doc_idx] if doc_idx < len(self.metadatas) else {},
                    "score": score,
                })
                
                if len(results) >= top_k:
                    break
            
            return results
        
        # 无向量索引，使用关键词匹配
        return self._keyword_match(query, top_k)
    
    def _chapter_aware_retrieve(self, query: str, top_k: int) -> List[Dict]:
        """
        章节感知检索
        
        检测查询是否包含书籍名+章节号，如果是则直接定位到对应 chunks。
        如果章节信息不完整，则使用语义检索作为备选。
        
        Args:
            query: 查询文本
            top_k: 返回条数
        
        Returns:
            检索结果列表，如果未检测到章节查询则返回 None
        """
        # 书籍别名映射（统一到章节索引中的书籍名）
        BOOK_ALIASES = {
            '红楼梦': 'hongloumeng',
            '石头记': 'hongloumeng',
            '金瓶梅': '金瓶梅',
        }
        
        def normalize_book_name(name: str) -> str:
            """标准化书名"""
            name = name.strip()
            # 先查别名
            for alias, canonical in BOOK_ALIASES.items():
                if alias in name:
                    return canonical
            return name
        
        # 章节查询模式
        chapter_patterns = [
            (r'《([^》]+)》第([一二三四五六七八九十百千万\d]+)回', '回'),
            (r'《([^》]+)》第([一二三四五六七八九十百千万\d]+)章', '章'),
            (r'([^《》]+)第([一二三四五六七八九十百千万\d]+)回', '回'),
            (r'([^《》]+)第([一二三四五六七八九十百千万\d]+)章', '章'),
        ]
        
        # 特殊处理红楼梦
        hlm_patterns = [
            (r'(红楼梦)[^第]*第([一二三四五六七八九十百千万\d]+)回', '回'),
            (r'(红楼梦)[^第]*第([一二三四五六七八九十百千万\d]+)章', '章'),
            (r'(红楼梦)\s*第([一二三四五六七八九十百千万\d]+)', '回'),
        ]
        
        # 中文数字映射
        cn_nums = {
            '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100, '千': 1000, '万': 10000,
        }

        def parse_num(num_str):
            """解析中文数字"""
            if num_str.isdigit():
                return int(num_str)
            result = 0
            temp = 0
            for char in num_str:
                if char in cn_nums:
                    val = cn_nums[char]
                    if val >= 100:
                        result = (result + temp) * val
                        temp = 0
                    elif val == 10:
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
        
        def search_chapter(book_name, chapter_num, chapter_type):
            """搜索章节"""
            # 1. 先查章节索引
            matched_book = None
            for book in self.chapter_index:
                if book_name in book or book in book_name:
                    matched_book = book
                    break
            
            if matched_book and matched_book in self.chapter_index:
                chapters = self.chapter_index[matched_book]
                for ch in chapters:
                    if ch['chapter_num'] == chapter_num:
                        chunk_idx = ch['chunk_idx']
                        if chunk_idx < len(self.documents):
                            return [{
                                "content": self.documents[chunk_idx],
                                "metadata": self.metadatas[chunk_idx],
                                "score": 1.0,
                                "chapter_info": f"{matched_book} 第{chapter_num}{chapter_type}",
                            }]
            
            # 2. 章节索引未命中，使用语义检索
            search_query = f"{book_name} 第{chapter_num}{chapter_type}"
            return self._semantic_search_books(search_query, book_name, top_k)
        
        def search_hlm_chapter(query, chapter_num, normalized_book):
            """搜索红楼梦章节"""
            # 使用标准化后的书名查找
            if normalized_book in self.chapter_index:
                chapters = self.chapter_index[normalized_book]
                for ch in chapters:
                    if ch['chapter_num'] == chapter_num:
                        chunk_idx = ch['chunk_idx']
                        if chunk_idx < len(self.documents):
                            return [{
                                "content": self.documents[chunk_idx],
                                "metadata": self.metadatas[chunk_idx],
                                "score": 1.0,
                                "chapter_info": f"红楼梦 第{chapter_num}回",
                            }]
            
            # 使用语义检索，使用传入的 query 作为搜索词
            return self._semantic_search_books(query, normalized_book, top_k)
        
        # 先检查红楼梦特殊模式
        for pattern, chapter_type in hlm_patterns:
            match = re.search(pattern, query)
            if match:
                book_name = match.group(1)
                chapter_str = match.group(2)
                chapter_num = parse_num(chapter_str)
                normalized_book = normalize_book_name(book_name)
                return search_hlm_chapter(query, chapter_num, normalized_book)
        
        # 检查通用章节模式
        for pattern, chapter_type in chapter_patterns:
            match = re.search(pattern, query)
            if match:
                book_name = match.group(1).strip()
                chapter_str = match.group(2)
                chapter_num = parse_num(chapter_str)
                return search_chapter(book_name, chapter_num, chapter_type)
        
        return None
    
    def _semantic_search_books(self, query: str, book_name: str, top_k: int) -> List[Dict]:
        """
        对特定书籍进行语义检索
        
        Args:
            query: 查询文本
            book_name: 书籍名称
            top_k: 返回条数
        
        Returns:
            检索结果列表
        """
        query_vec = self._encode_text(query)
        
        if self.vectors is None:
            return []
        
        # 获取该书籍的所有 chunks
        book_indices = []
        for i, meta in enumerate(self.metadatas):
            source = meta.get('source', '')
            if book_name in source or source in book_name:
                book_indices.append(i)
        
        if not book_indices:
            return []
        
        # 计算相似度
        similarities = []
        for idx in book_indices:
            if self.vector_doc_indices is not None:
                # 找到向量索引中的位置
                for vi, di in enumerate(self.vector_doc_indices):
                    if di == idx:
                        similarities.append((vi, idx, float(np.dot(self.vectors[vi], query_vec))))
                        break
            else:
                if idx < len(self.vectors):
                    similarities.append((idx, idx, float(np.dot(self.vectors[idx], query_vec))))
        
        # 排序
        similarities.sort(key=lambda x: -x[2])
        
        results = []
        for _, doc_idx, score in similarities[:top_k]:
            results.append({
                "content": self.documents[doc_idx],
                "metadata": self.metadatas[doc_idx],
                "score": score,
                "chapter_info": f"{book_name} 相关内容",
            })
        
        return results
    
    def _keyword_match(self, query: str, top_k: int) -> List[Dict]:
        """关键词匹配（备选方案）- 无需 jieba"""
        # 简单字符级关键词匹配
        query_lower = query.lower()
        query_chars = set(query_lower)
        
        results = []
        for i, doc in enumerate(self.documents):
            doc_lower = doc.lower()
            doc_chars = set(doc_lower)
            
            # 字符级 Jaccard 相似度
            intersection = len(query_chars & doc_chars)
            union = len(query_chars | doc_chars)
            
            # 额外检查连续词匹配
            word_score = 0
            words = query.split()
            for word in words:
                if word in doc_lower:
                    word_score += len(word)
            
            # 综合分数
            char_sim = intersection / union if union > 0 else 0
            score = char_sim * 0.3 + (word_score / len(query)) * 0.7
            
            if score > 0.01:  # 最低阈值
                results.append({
                    "content": doc,
                    "metadata": self.metadatas[i] if i < len(self.metadatas) else {},
                    "score": score,
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    def format_knowledge_context(
        self,
        results: List[Dict],
        max_len: int = 5000,
    ) -> str:
        """
        格式化检索结果为上下文

        Args:
            results: 检索结果
            max_len: 最大字符数

        Returns:
            格式化的上下文字符串
        """
        if not results:
            return ""

        context_parts = []

        total_len = 0
        for i, r in enumerate(results, 1):
            content = r["content"]
            metadata = r.get("metadata", {})
            chapter_info = r.get("chapter_info", "")
            source = metadata.get("source", "")

            # 格式化
            header = f"【{source}】"
            if chapter_info:
                header = f"【{source} - {chapter_info}】"

            entry = f"{header}\n{content}"

            if total_len + len(entry) <= max_len:
                context_parts.append(entry)
                total_len += len(entry)
            else:
                # 截断最后一个
                remaining = max_len - total_len - 20
                if remaining > 100:
                    context_parts.append(entry[:remaining] + "...")
                break

        return "\n\n".join(context_parts)


def get_rag_retriever() -> SimpleRAGRetriever:
    """获取 RAG 检索器实例"""
    return SimpleRAGRetriever.get_instance()


def retrieve_knowledge(
    query: str,
    top_k: int = 3,
    include_context: bool = True,
) -> Tuple[List[Dict], str]:
    """
    检索知识的便捷函数
    
    Args:
        query: 查询文本
        top_k: 返回条数
        include_context: 是否返回格式化上下文
    
    Returns:
        (原始检索结果, 格式化上下文)
    """
    retriever = get_rag_retriever()
    results = retriever.retrieve(query, top_k=top_k)
    context = retriever.format_knowledge_context(results) if include_context else ""
    return results, context


# ═══════════════════════════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("RAG 检索测试")
    print("=" * 60)
    
    # 测试检索
    retriever = get_rag_retriever()
    
    test_queries = [
        "朋友心情不好怎么办",
        "如何改善失眠",
        "怎样建立自信",
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        results, context = retrieve_knowledge(query, top_k=2)
        print(f"检索到 {len(results)} 条结果")
        print(context[:300])
        print("-" * 40)

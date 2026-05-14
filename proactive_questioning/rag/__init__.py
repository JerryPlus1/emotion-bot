"""
RAG 模块：检索增强生成相关功能。

子模块：
- rag_utils: RAG 检索器核心实现
- build_rag_index: 构建知识库索引
- build_chapter_index: 构建章节索引
- build_full_index: 构建全文索引
- build_hongloumeng_index: 红楼梦索引构建
"""

from .rag_utils import (
    SimpleRAGRetriever,
    get_rag_retriever,
    retrieve_knowledge,
)

__all__ = [
    "SimpleRAGRetriever",
    "get_rag_retriever",
    "retrieve_knowledge",
]

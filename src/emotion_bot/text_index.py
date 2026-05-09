"""Embedding and local text index utilities."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import Counter
from functools import lru_cache
from typing import Iterable

VECTOR_DIMENSIONS = 2048
_LATIN_RE = re.compile(r"[a-zA-Z0-9_]+")
_CHAPTER_RE = re.compile(r"第?([一二三四五六七八九十百千万〇零两\d]+)章")
Vector = dict[int, float] | list[float]


def _is_cjk(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"


def tokenize(text: str) -> list[str]:
    normalized = text.lower()
    latin_tokens = _LATIN_RE.findall(normalized)

    cjk_chars: list[str] = []
    for char in normalized:
        if _is_cjk(char):
            cjk_chars.append(char)
        else:
            cjk_chars.append(" ")

    cjk_text = "".join(cjk_chars)
    cjk_tokens: list[str] = []
    for part in cjk_text.split():
        cjk_tokens.extend(part)
        cjk_tokens.extend(part[index : index + 2] for index in range(max(len(part) - 1, 0)))
        cjk_tokens.extend(part[index : index + 3] for index in range(max(len(part) - 2, 0)))

    return [token for token in latin_tokens + cjk_tokens if token.strip()]


def _hash_token(token: str) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big") % VECTOR_DIMENSIONS


class BaseEmbeddingModel:
    backend_name = "base"

    def embed(self, text: str) -> Vector:
        raise NotImplementedError


class HashingEmbeddingModel(BaseEmbeddingModel):
    backend_name = "hashing"

    def embed(self, text: str) -> dict[int, float]:
        return sparse_embedding(text)


class FastEmbedEmbeddingModel(BaseEmbeddingModel):
    backend_name = "fastembed"

    def __init__(self, model_name: str):
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise RuntimeError("fastembed is not installed") from exc
        self.model_name = model_name
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, text: str) -> list[float]:
        vectors = list(self._model.embed([text]))
        if not vectors:
            return []
        vector = vectors[0]
        norm = math.sqrt(sum(float(value) * float(value) for value in vector))
        if norm == 0:
            return []
        return [float(value) / norm for value in vector]


@lru_cache(maxsize=1)
def get_embedding_model() -> BaseEmbeddingModel:
    backend = os.getenv("EMOTION_BOT_EMBEDDING_BACKEND", "auto").lower()
    model_name = os.getenv("EMOTION_BOT_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    if backend in {"fastembed", "auto"}:
        try:
            return FastEmbedEmbeddingModel(model_name)
        except Exception:
            if backend == "fastembed":
                raise
    return HashingEmbeddingModel()


def embedding_backend_name() -> str:
    model = get_embedding_model()
    if isinstance(model, FastEmbedEmbeddingModel):
        return f"{model.backend_name}:{model.model_name}"
    return model.backend_name


def embed_text(text: str) -> Vector:
    return get_embedding_model().embed(text)


def sparse_embedding(text: str) -> dict[int, float]:
    counts = Counter(tokenize(text))
    if not counts:
        return {}

    weighted: dict[int, float] = {}
    for token, count in counts.items():
        index = _hash_token(token)
        weighted[index] = weighted.get(index, 0.0) + 1.0 + math.log(count)

    norm = math.sqrt(sum(value * value for value in weighted.values()))
    if norm == 0:
        return {}
    return {index: value / norm for index, value in weighted.items()}


def cosine_similarity(left: Vector, right: Vector) -> float:
    if not left or not right:
        return 0.0
    if isinstance(left, dict) and isinstance(right, dict):
        if len(left) > len(right):
            left, right = right, left
        return sum(value * right.get(index, 0.0) for index, value in left.items())
    if isinstance(left, list) and isinstance(right, list):
        return sum(left_value * right_value for left_value, right_value in zip(left, right))
    return 0.0


def serialize_vector(vector: Vector) -> str:
    if isinstance(vector, dict):
        value = {str(key): item for key, item in vector.items()}
    else:
        value = vector
    return json.dumps(value, ensure_ascii=False)


def deserialize_vector(raw: str | None) -> Vector:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if isinstance(value, list):
        return [float(item) for item in value]
    if isinstance(value, dict):
        return {int(key): float(item) for key, item in value.items()}
    return {}


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    clean = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not clean:
        return []
    if len(clean) <= chunk_size:
        return [clean]

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunks.append(clean[start:end])
        if end == len(clean):
            break
        start = max(end - overlap, start + 1)
    return chunks


def keyword_overlap(query: str, text: str) -> float:
    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(text))
    if not query_tokens or not text_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / math.sqrt(len(query_tokens) * len(text_tokens))


def requested_chapter_heading(query: str) -> str | None:
    compact = re.sub(r"\s+", "", query)
    match = _CHAPTER_RE.search(compact)
    if not match:
        return None
    return f"第{match.group(1)}章"


def chapter_heading_score(query: str, text: str) -> float:
    heading = requested_chapter_heading(query)
    if not heading:
        return 0.0
    has_any_heading = False
    for line in text.splitlines():
        normalized = re.sub(r"[\s　]+", "", line)
        if not normalized:
            continue
        if normalized == heading:
            return 3.0
        if _CHAPTER_RE.fullmatch(normalized):
            has_any_heading = True
    if heading in text:
        return 0.2
    if has_any_heading:
        return -0.15
    return 0.0


def rank_texts(query: str, texts: Iterable[tuple[str, float]]) -> list[tuple[str, float]]:
    query_vector = embed_text(query)
    ranked: list[tuple[str, float]] = []
    for text, weight in texts:
        vector_score = cosine_similarity(query_vector, embed_text(text))
        overlap_score = keyword_overlap(query, text)
        ranked.append((text, (vector_score * 0.75 + overlap_score * 0.25 + chapter_heading_score(query, text)) * weight))
    return sorted(ranked, key=lambda item: item[1], reverse=True)

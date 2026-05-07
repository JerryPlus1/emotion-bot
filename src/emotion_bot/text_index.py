"""Small local text index utilities.

The project should work offline with only the GGUF chat model available. For
RAG and memory recall we therefore use a deterministic sparse embedding based
on token hashing. It is not a replacement for a semantic embedding model, but
it gives useful, explainable retrieval without another large dependency.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from typing import Iterable

VECTOR_DIMENSIONS = 2048
_LATIN_RE = re.compile(r"[a-zA-Z0-9_]+")


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


def cosine_similarity(left: dict[int, float], right: dict[int, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(index, 0.0) for index, value in left.items())


def serialize_vector(vector: dict[int, float]) -> str:
    return json.dumps({str(key): value for key, value in vector.items()}, ensure_ascii=False)


def deserialize_vector(raw: str | None) -> dict[int, float]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return {int(key): float(item) for key, item in value.items()}


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


def rank_texts(query: str, texts: Iterable[tuple[str, float]]) -> list[tuple[str, float]]:
    query_vector = sparse_embedding(query)
    ranked: list[tuple[str, float]] = []
    for text, weight in texts:
        vector_score = cosine_similarity(query_vector, sparse_embedding(text))
        overlap_score = keyword_overlap(query, text)
        ranked.append((text, (vector_score * 0.75 + overlap_score * 0.25) * weight))
    return sorted(ranked, key=lambda item: item[1], reverse=True)

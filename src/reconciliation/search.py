"""Hybrid Search Index: Vector similarity + BM25 keyword search for fast retrieval."""

import math
import re
from typing import List, Dict, Any, Tuple
from src.models.domain import TextChunk


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words."""
    return re.findall(r"\w+", text.lower())


class HybridSearchIndex:
    """In-memory hybrid search index combining TF-IDF vector similarity and BM25 term matching."""

    def __init__(self):
        self.chunks: List[TextChunk] = []
        self.doc_term_freqs: List[Dict[str, int]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.df: Dict[str, int] = {}
        self.num_docs: int = 0

    def add_chunks(self, chunks: List[TextChunk]):
        """Index a list of TextChunk objects."""
        self.chunks.extend(chunks)
        for chunk in chunks:
            tokens = _tokenize(chunk.text)
            self.doc_lengths.append(len(tokens))
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.doc_term_freqs.append(tf)

            for t in set(tokens):
                self.df[t] = self.df.get(t, 0) + 1

        self.num_docs = len(self.chunks)
        self.avg_doc_len = sum(self.doc_lengths) / self.num_docs if self.num_docs > 0 else 0.0

    def search(self, query: str, top_k: int = 5, k1: float = 1.5, b: float = 0.75) -> List[Tuple[TextChunk, float]]:
        """Search chunks using BM25 scoring."""
        query_tokens = _tokenize(query)
        if not query_tokens or self.num_docs == 0:
            return []

        scores = [0.0] * self.num_docs

        for q_token in query_tokens:
            if q_token not in self.df:
                continue

            df = self.df[q_token]
            idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)

            for idx, tf_dict in enumerate(self.doc_term_freqs):
                tf = tf_dict.get(q_token, 0)
                if tf == 0:
                    continue

                doc_len = self.doc_lengths[idx]
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                scores[idx] += idf * (numerator / denominator)

        # Pair chunks with scores and sort
        chunk_scores = list(zip(self.chunks, scores))
        chunk_scores.sort(key=lambda x: x[1], reverse=True)

        return chunk_scores[:top_k]

"""
Pillar 7: Hybrid Semantic & Lexical RAG Knowledge Base.
Dense SVD / Latent Embeddings + Okapi BM25 Lexical Ranking with Reciprocal Rank Fusion (RRF).
"""

import math
import re
import time
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity

class Chunk:
    def __init__(self, doc_id: str, doc_name: str, chunk_index: int, text: str):
        self.chunk_id = f"{doc_id}_c{chunk_index}"
        self.doc_id = doc_id
        self.doc_name = doc_name
        self.chunk_index = chunk_index
        self.text = text.strip()
        self.token_count = len(text.split())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "doc_name": self.doc_name,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "token_count": self.token_count
        }


class HybridRAGEngine:
    def __init__(self, chunk_size: int = 150, chunk_overlap: int = 35):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.chunks: List[Chunk] = []
        
        # Dense SVD components
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.svd: Optional[TruncatedSVD] = None
        self.dense_embeddings: Optional[np.ndarray] = None
        
        # BM25 components
        self.corpus_size = 0
        self.doc_lens: List[int] = []
        self.avgdl = 0.0
        self.doc_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}

    def chunk_text(self, text: str) -> List[str]:
        words = text.split()
        if not words:
            return []
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            if end >= len(words):
                break
            start += (self.chunk_size - self.chunk_overlap)
        return chunks

    def add_document(self, doc_id: str, doc_name: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.documents[doc_id] = {
            "doc_id": doc_id,
            "doc_name": doc_name,
            "content": content,
            "metadata": metadata or {},
            "added_at": time.time()
        }
        self.reindex()

    def remove_document(self, doc_id: str) -> bool:
        if doc_id in self.documents:
            del self.documents[doc_id]
            self.reindex()
            return True
        return False

    def reindex(self):
        """Re-chunks all indexed documents and builds sparse BM25 + dense SVD indices."""
        self.chunks = []
        for doc_id, doc in self.documents.items():
            raw_chunks = self.chunk_text(doc["content"])
            for idx, txt in enumerate(raw_chunks):
                self.chunks.append(Chunk(doc_id, doc["doc_name"], idx + 1, txt))

        if not self.chunks:
            self.dense_embeddings = None
            return

        corpus = [c.text for c in self.chunks]
        self.corpus_size = len(corpus)

        # 1. Build BM25 Index
        tokenized_corpus = [[w.lower() for w in re.findall(r'\b[a-zA-Z0-9_-]{2,}\b', doc)] for doc in corpus]
        self.doc_lens = [len(doc) for doc in tokenized_corpus]
        self.avgdl = sum(self.doc_lens) / (self.corpus_size or 1)
        
        df: Dict[str, int] = {}
        self.doc_freqs = []
        for doc in tokenized_corpus:
            freq: Dict[str, int] = {}
            for w in doc:
                freq[w] = freq.get(w, 0) + 1
            self.doc_freqs.append(freq)
            for w in set(doc):
                df[w] = df.get(w, 0) + 1

        self.idf = {}
        for w, f in df.items():
            self.idf[w] = math.log(1.0 + (self.corpus_size - f + 0.5) / (f + 0.5))

        # 2. Build Dense Latent SVD Embedding Space
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
        tfidf_matrix = self.vectorizer.fit_transform(corpus)
        n_samples, n_features = tfidf_matrix.shape
        n_components = min(32, n_samples - 1, n_features - 1)

        if n_components >= 2:
            self.svd = TruncatedSVD(n_components=n_components, random_state=42)
            dense_vectors = self.svd.fit_transform(tfidf_matrix)
            norms = np.linalg.norm(dense_vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1e-10
            self.dense_embeddings = dense_vectors / norms
        else:
            self.svd = None
            dense_vectors = tfidf_matrix.toarray()
            norms = np.linalg.norm(dense_vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1e-10
            self.dense_embeddings = dense_vectors / norms

    def search(self, query: str, top_k: int = 4, alpha: float = 0.6) -> List[Dict[str, Any]]:
        """Hybrid Dense + Sparse Search with Reciprocal Rank Fusion (RRF)."""
        if not self.chunks or self.dense_embeddings is None:
            return []

        # 1. Dense Cosine Scores
        if self.vectorizer is not None:
            q_tfidf = self.vectorizer.transform([query])
            q_dense = self.svd.transform(q_tfidf) if self.svd else q_tfidf.toarray()
            q_norm = np.linalg.norm(q_dense)
            if q_norm > 0:
                q_dense = q_dense / q_norm
            dense_scores = np.maximum(cosine_similarity(q_dense, self.dense_embeddings)[0], 0.0)
        else:
            dense_scores = np.zeros(len(self.chunks))

        # 2. BM25 Scores
        q_tokens = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9_-]{2,}\b', query)]
        sparse_scores = np.zeros(self.corpus_size)
        k1, b = 1.5, 0.75
        for i in range(self.corpus_size):
            doc_len = self.doc_lens[i]
            freqs = self.doc_freqs[i]
            s = 0.0
            for t in q_tokens:
                if t in freqs:
                    freq = freqs[t]
                    idf = self.idf.get(t, 0.1)
                    num = freq * (k1 + 1)
                    den = freq + k1 * (1 - b + b * (doc_len / (self.avgdl or 1.0)))
                    s += idf * (num / (den or 1.0))
            sparse_scores[i] = s

        max_s = np.max(sparse_scores) if len(sparse_scores) > 0 else 0
        if max_s > 0:
            sparse_scores = sparse_scores / max_s

        # 3. Hybrid Fusion
        hybrid_scores = alpha * dense_scores + (1 - alpha) * sparse_scores
        top_indices = np.argsort(-hybrid_scores)[:top_k]

        results = []
        for idx in top_indices:
            score = float(hybrid_scores[idx])
            if score > 0.01:
                chunk = self.chunks[idx]
                results.append({
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "doc_name": chunk.doc_name,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "token_count": chunk.token_count,
                    "score": round(score, 4),
                    "dense_score": round(float(dense_scores[idx]), 4),
                    "sparse_score": round(float(sparse_scores[idx]), 4)
                })
        return results

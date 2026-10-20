import os
import re
import numpy as np
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.rag.ingestion import DocumentChunk, load_all_industrial_documents

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents")

def simple_tokenize(text: str) -> List[str]:
    """Lowercase word tokenizer that preserves fault codes like P-104, SKF 6205, BPFI."""
    return re.findall(r"\b[A-Za-z0-9\-_]+\b", text.lower())

class HybridIndustrialRetriever:
    """
    Hybrid retriever combining BM25 lexical token matching with TF-IDF n-gram vector
    cosine similarity and Reciprocal Rank Fusion (RRF) reranking.
    Note: TF-IDF is a statistical sparse n-gram vector representation, not a dense neural embedding.
    """

    def __init__(self, documents_dir: str = DOCS_DIR):
        self.documents_dir = documents_dir
        self.chunks: List[DocumentChunk] = []
        self.bm25: Optional[BM25Okapi] = None
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.load_and_index()

    def load_and_index(self):
        """Load and index all documents from directory."""
        if os.path.exists(self.documents_dir):
            self.chunks = load_all_industrial_documents(self.documents_dir)
        else:
            self.chunks = []

        if not self.chunks:
            return

        # 1. Build BM25 Index (lexical token matching preserving asset codes)
        corpus_tokenized = [simple_tokenize(chunk.content + " " + chunk.title + " " + chunk.section) for chunk in self.chunks]
        self.bm25 = BM25Okapi(corpus_tokenized)

        # 2. Build TF-IDF Vector Index (sparse statistical n-gram term frequency representation)
        corpus_text = [
            f"{c.title} {c.section} {c.equipment_model} {c.content}"
            for c in self.chunks
        ]
        self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus_text)

    def retrieve(
        self,
        query: str,
        asset_id: Optional[str] = None,
        top_k: int = 4,
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Execute hybrid retrieval combining BM25 lexical ranking and TF-IDF statistical vector
        similarity with Reciprocal Rank Fusion (RRF).
        """
        if not self.chunks or self.bm25 is None or self.tfidf_vectorizer is None:
            return []

        # 1. BM25 Lexical Ranking
        query_tokens = simple_tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_ranked_indices = np.argsort(bm25_scores)[::-1]

        # 2. TF-IDF Statistical Vector Cosine Similarity Ranking
        query_vec = self.tfidf_vectorizer.transform([query])
        tfidf_sims = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        tfidf_ranked_indices = np.argsort(tfidf_sims)[::-1]

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[int, float] = {i: 0.0 for i in range(len(self.chunks))}
        
        for rank, idx in enumerate(bm25_ranked_indices):
            rrf_scores[idx] += 1.0 / (rrf_k + rank + 1)
            
        for rank, idx in enumerate(tfidf_ranked_indices):
            rrf_scores[idx] += 1.0 / (rrf_k + rank + 1)

        # Boost matching equipment model if asset_id is provided
        if asset_id:
            asset_norm = asset_id.lower().replace("-", "")
            for idx, chunk in enumerate(self.chunks):
                chunk_equip = chunk.equipment_model.lower().replace("-", "")
                if asset_norm in chunk_equip or "sop" in chunk.document_type.lower():
                    rrf_scores[idx] *= 1.25  # 25% relevance boost for asset-specific or general SOP chunks

        # Sort by final fused score
        sorted_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)
        top_indices = sorted_indices[:top_k]

        results = []
        for rank_pos, idx in enumerate(top_indices):
            chunk = self.chunks[idx]
            results.append({
                "rank": rank_pos + 1,
                "score": round(float(rrf_scores[idx]), 4),
                "bm25_score": round(float(bm25_scores[idx]), 3),
                "tfidf_score": round(float(tfidf_sims[idx]), 3),
                "dense_score": round(float(tfidf_sims[idx]), 3),  # Alias preserved for backwards compatibility
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "title": chunk.title,
                "section": chunk.section,
                "equipment_model": chunk.equipment_model,
                "document_type": chunk.document_type,
                "revision_date": chunk.revision_date,
                "passage": chunk.content
            })

        return results

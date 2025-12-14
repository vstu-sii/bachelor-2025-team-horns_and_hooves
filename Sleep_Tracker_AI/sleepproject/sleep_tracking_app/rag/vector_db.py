# sleep_tracking_app/rag/vector_db.py
import os
import time
import hashlib
from typing import List, Dict, Any, Optional

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "sleep_research_articles")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-albert-small-v2")


class SleepVectorDB:
    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT, collection: str = QDRANT_COLLECTION):
        self.client = QdrantClient(host=host, port=port, timeout=30)
        self.collection_name = collection
        # Загрузка модели эмбеддингов (скачивается при первом запуске)
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self._init_collection()

    def _init_collection(self) -> None:
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection_name not in collections:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.embedding_model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                )
        except Exception as e:
            raise RuntimeError(f"Qdrant init failed: {e}")

    def _make_id(self, text_id: str) -> int:
        return int(hashlib.md5(text_id.encode()).hexdigest()[:16], 16)

    def upsert_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 100):
        """
        chunks: list of {'id': '...', 'text': '...', 'meta': {...}}
        """
        points = []
        for ch in chunks:
            emb = self.embedding_model.encode(ch["text"]).tolist()
            pid = self._make_id(ch["id"])
            points.append(PointStruct(id=pid, vector=emb, payload={**ch.get("meta", {}), "text": ch["text"]}))

            if len(points) >= batch_size:
                self.client.upsert(collection_name=self.collection_name, wait=True, points=points)
                points = []
        if points:
            self.client.upsert(collection_name=self.collection_name, wait=True, points=points)

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        q_emb = self.embedding_model.encode(query).tolist()
        # Для разных версий qdrant API используем query_points или search:
        try:
            results = self.client.search(collection_name=self.collection_name, query_vector=q_emb, limit=limit)
            formatted = []
            for hit in results:
                formatted.append({
                    "score": hit.score,
                    "text": hit.payload.get("text", ""),
                    "source": hit.payload.get("source", ""),
                    "chunk_id": hit.payload.get("chunk_id", "")
                })
            return formatted
        except Exception:
            # Попытка совместимости
            res = self.client.search(collection_name=self.collection_name, query_vector=q_emb, limit=limit)
            formatted = []
            for hit in res:
                formatted.append({
                    "score": getattr(hit, "score", 0),
                    "text": hit.payload.get("text", ""),
                    "source": hit.payload.get("source", ""),
                    "chunk_id": hit.payload.get("chunk_id", "")
                })
            return formatted

    def get_stats(self) -> Dict[str, Any]:
        info = self.client.get_collection(self.collection_name)
        return {"points_count": info.points_count, "collection_name": self.collection_name}

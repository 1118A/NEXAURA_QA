import logging
from typing import List
from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL_NAME
from app.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        try:
            logger.info(f"Initializing SentenceTransformer model: {EMBEDDING_MODEL_NAME}...")
            self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.info("SentenceTransformer model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformer model: {str(e)}")
            raise EmbeddingError(f"Embedding model initialization failed: {str(e)}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            logger.info(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error computing text embeddings: {str(e)}")
            raise EmbeddingError(f"Failed to generate text embeddings: {str(e)}")

    def embed_query(self, query: str) -> List[float]:
        if not query.strip():
            raise EmbeddingError("Empty query provided for embedding.")
        try:
            embedding = self.model.encode(
                [query],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embedding[0].tolist()
        except Exception as e:
            logger.error(f"Error computing query embedding: {str(e)}")
            raise EmbeddingError(f"Failed to generate query embedding: {str(e)}")

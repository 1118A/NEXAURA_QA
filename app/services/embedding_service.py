import logging
import httpx
from typing import List

from app.config import JINA_API_KEY
from app.exceptions import EmbeddingError

logger = logging.getLogger(__name__)

# Jina AI embedding model — 768-dimensional, fast, free tier: 1M tokens/month
JINA_MODEL = "jina-embeddings-v2-base-en"
JINA_ENDPOINT = "https://api.jina.ai/v1/embeddings"


class EmbeddingService:
    def __init__(self):
        if not JINA_API_KEY:
            raise EmbeddingError(
                "JINA_API_KEY is not configured. "
                "Get a free key at https://jina.ai"
            )
        self.headers = {
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json",
        }
        logger.info(f"EmbeddingService ready — using Jina AI model '{JINA_MODEL}' (API-based).")

    def _call_api(self, texts: List[str]) -> List[List[float]]:
        """Call Jina AI embeddings endpoint and return list of embedding vectors."""
        payload = {"model": JINA_MODEL, "input": texts}
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(JINA_ENDPOINT, headers=self.headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise EmbeddingError(
                f"Jina AI API request failed (HTTP {e.response.status_code}): {e.response.text}"
            )
        except httpx.RequestError as e:
            raise EmbeddingError(f"Network error calling Jina AI API: {str(e)}")

        data = response.json().get("data", [])
        # Sort by index to preserve original order
        data.sort(key=lambda x: x["index"])
        return [item["embedding"] for item in data]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        logger.info(f"Generating embeddings for {len(texts)} chunks via Jina AI...")
        try:
            # Jina allows up to 2048 items per request — batch if needed
            batch_size = 128
            all_embeddings: List[List[float]] = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                all_embeddings.extend(self._call_api(batch))
            return all_embeddings
        except EmbeddingError:
            raise
        except Exception as e:
            logger.error(f"Error computing text embeddings: {str(e)}")
            raise EmbeddingError(f"Failed to generate text embeddings: {str(e)}")

    def embed_query(self, query: str) -> List[float]:
        if not query.strip():
            raise EmbeddingError("Empty query provided for embedding.")
        try:
            embeddings = self._call_api([query])
            return embeddings[0]
        except EmbeddingError:
            raise
        except Exception as e:
            logger.error(f"Error computing query embedding: {str(e)}")
            raise EmbeddingError(f"Failed to generate query embedding: {str(e)}")

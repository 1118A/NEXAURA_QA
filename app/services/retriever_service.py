import logging
from typing import List, Dict, Any

from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)

class RetrieverService:
    def __init__(self, embedding_service: EmbeddingService, vector_store_service: VectorStoreService):
        self.embedding_service = embedding_service
        self.vector_store_service = vector_store_service

    def retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = 4,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        logger.info(f"Retrieving code snippets for: '{query}' (top_k={top_k}, threshold={similarity_threshold})")
        
        # 1. Get vector embedding of user query
        query_embedding = self.embedding_service.embed_query(query)
        
        # 2. Query the vector store
        # Fetch slightly more than top_k to allow filtering by threshold
        raw_results = self.vector_store_service.search(query_embedding, top_k=max(top_k * 2, 8))
        
        # 3. Filter by similarity threshold
        filtered_results = []
        for item in raw_results:
            score = item.get("score", 0.0)
            if score >= similarity_threshold:
                filtered_results.append(item)
            else:
                logger.debug(f"Filtered out snippet from {item['metadata']['relative_path']} with score {score:.4f} < {similarity_threshold}")
                
        # 4. Sort in descending order of similarity score and limit to top_k
        filtered_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        final_results = filtered_results[:top_k]
        
        logger.info(f"Retrieved {len(final_results)} relevant code chunks after filtering.")
        return final_results

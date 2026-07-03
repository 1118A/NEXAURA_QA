import logging
import chromadb  # chromadb-client package (HTTP-only, no local ML deps)
from typing import List, Dict, Any

from app.config import (
    CHROMA_API_KEY,
    CHROMA_TENANT,
    CHROMA_DATABASE,
    CHROMA_COLLECTION_NAME,
    UPSERT_BATCH_SIZE,
)
from app.models.schemas import CodeChunk
from app.exceptions import VectorStoreError

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        # Configuration check
        if not all([CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE]):
            logger.error("Chroma Cloud configuration variables are missing.")
            raise VectorStoreError(
                "Chroma Cloud credentials or database parameters are missing from environment config.",
                code="CHROMA_CONFIG_MISSING"
            )

        try:
            logger.info("Connecting to Chroma Cloud Client...")
            self.client = chromadb.CloudClient(
                api_key=CHROMA_API_KEY,
                tenant=CHROMA_TENANT,
                database=CHROMA_DATABASE,
            )
            
            logger.info(f"Retrieving or creating collection '{CHROMA_COLLECTION_NAME}'...")
            self.collection = self.client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Chroma connection established successfully.")
        except Exception as e:
            logger.error(f"Chroma connection failed: {str(e)}")
            raise VectorStoreError(
                f"Failed to connect to Chroma Cloud database: {str(e)}",
                code="CHROMA_CONNECTION_FAILURE"
            )

    def add_chunks(self, chunks: List[CodeChunk], embeddings: List[List[float]]) -> None:
        if not chunks or not embeddings:
            logger.warning("Empty chunks or embeddings passed to vector store.")
            return

        if len(chunks) != len(embeddings):
            raise VectorStoreError(
                f"Mismatch between number of chunks ({len(chunks)}) and embeddings ({len(embeddings)}).",
                code="CHROMA_UPSERT_MISMATCH"
            )

        ids = []
        documents = []
        metadatas = []
        filtered_embeddings = []

        for chunk, embedding in zip(chunks, embeddings):
            ids.append(chunk.chunk_id)
            documents.append(chunk.content)
            filtered_embeddings.append(embedding)

            # Build metadata dictionary ensuring no None values for key fields
            metadatas.append({
                "file_path": chunk.file_path,
                "relative_path": chunk.relative_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "symbol_name": chunk.symbol_name or "",
                "symbol_type": chunk.symbol_type,
                "language": chunk.language,
            })

        logger.info(f"Upserting {len(ids)} chunks to Chroma Cloud in batches of {UPSERT_BATCH_SIZE}...")
        
        try:
            for i in range(0, len(ids), UPSERT_BATCH_SIZE):
                batch_end = min(i + UPSERT_BATCH_SIZE, len(ids))
                logger.info(f"Upserting batch {i} to {batch_end}...")
                self.collection.upsert(
                    ids=ids[i:batch_end],
                    documents=documents[i:batch_end],
                    embeddings=filtered_embeddings[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                )
            logger.info("Batch upsert completed successfully.")
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Chroma upsert failed: {err_msg}")
            
            if "quota" in err_msg.lower() or "limit" in err_msg.lower():
                raise VectorStoreError(
                    "Chroma Cloud storage quota exceeded. Please clean up or upgrade your database storage.",
                    code="CHROMA_QUOTA_EXCEEDED"
                )
            else:
                raise VectorStoreError(
                    f"Failed to upsert code chunks to database: {err_msg}",
                    code="CHROMA_UPSERT_ERROR"
                )

    def search(self, query_embedding: List[float], top_k: int = 4) -> List[Dict[str, Any]]:
        try:
            logger.info(f"Searching Chroma Cloud collection for top {top_k} matches...")
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            items = []
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for doc, meta, distance in zip(documents, metadatas, distances):
                # distance is cosine distance, so similarity score is 1 - distance
                score = 1.0 - float(distance)
                items.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": distance,
                    "score": score,
                })
            
            logger.info(f"Found {len(items)} matching results.")
            return items
        except Exception as e:
            logger.error(f"Chroma query failed: {str(e)}")
            raise VectorStoreError(
                f"Failed to query vector database: {str(e)}",
                code="CHROMA_QUERY_ERROR"
            )

    def reset(self) -> None:
        try:
            logger.info(f"Resetting collection '{CHROMA_COLLECTION_NAME}'...")
            try:
                self.client.delete_collection(CHROMA_COLLECTION_NAME)
                logger.info(f"Deleted old collection '{CHROMA_COLLECTION_NAME}'")
            except Exception:
                # Catch if collection doesn't exist
                pass

            self.collection = self.client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Recreated collection '{CHROMA_COLLECTION_NAME}' successfully.")
        except Exception as e:
            logger.error(f"Chroma reset failed: {str(e)}")
            raise VectorStoreError(
                f"Failed to reset vector database collection: {str(e)}",
                code="CHROMA_RESET_ERROR"
            )

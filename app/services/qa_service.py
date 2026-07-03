import logging
from typing import List, Dict, Any, Tuple
from groq import Groq, BadRequestError, AuthenticationError

from app.config import GROQ_API_KEY, GROQ_MODEL, MAX_CHUNK_CHARS
from app.exceptions import LLMError

logger = logging.getLogger(__name__)

class QAService:
    def __init__(self):
        if not GROQ_API_KEY:
            logger.error("Groq API key is missing.")
            raise LLMError(
                "Groq API key is missing. Please add GROQ_API_KEY in your .env file.",
                code="GROQ_KEY_MISSING"
            )
        try:
            logger.info("Initializing Groq client...")
            self.client = Groq(api_key=GROQ_API_KEY)
            logger.info("Groq client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")
            raise LLMError(f"Groq client initialization failed: {str(e)}", code="GROQ_INIT_FAILED")

    def build_context(self, retrieved_chunks: List[Dict[str, Any]], max_context_chars: int) -> Tuple[str, List[Dict[str, Any]]]:
        """Construct context blocks while respecting max character constraints."""
        context_blocks = []
        used_chunks = []
        current_chars = 0
        
        for index, chunk in enumerate(retrieved_chunks, start=1):
            metadata = chunk["metadata"]
            content = chunk["content"]
            
            # Truncate chunk content if it is uniquely larger than MAX_CHUNK_CHARS
            if len(content) > MAX_CHUNK_CHARS:
                content = content[:MAX_CHUNK_CHARS] + "\n\n...[code block truncated]..."
                
            block = f"========== Source {index} ==========\n"
            block += f"File: {metadata['relative_path']}\n"
            block += f"Lines: {metadata['start_line']} - {metadata['end_line']}\n"
            if metadata.get("symbol_name"):
                block += f"Symbol: {metadata['symbol_name']} ({metadata.get('symbol_type', 'unknown')})\n"
            block += f"\n{content}\n\n"
            
            block_len = len(block)
            # Check if adding this block violates the context size control
            if current_chars + block_len > max_context_chars:
                logger.warning(f"Context character limit reached ({max_context_chars}). Skipping remaining chunks.")
                break
                
            context_blocks.append(block)
            used_chunks.append(chunk)
            current_chars += block_len
            
        return "\n".join(context_blocks), used_chunks

    def build_prompt(self, question: str, context: str) -> str:
        return f"""You are an expert Software Engineer pair programming with the user.

Your task is to answer the user's question about the codebase ONLY using the provided Repository Context below.

Rules you MUST follow:
1. NEVER hallucinate information. If the answer cannot be found in the provided Repository Context, reply EXACTLY with:
"I could not find this information in the indexed repository."
Do not attempt to write code from scratch or use external knowledge if the context is insufficient.

2. Restrict your answer ONLY to the code snippets retrieved.

3. When referencing code files or lines in your explanation, always cite them exactly in the format "filename:start-end" (e.g. routes.py:15-22).

4. Keep your answers concise, clear, and highly technical.

User Question:
{question}

=========================
Repository Context
=========================
{context}
"""

    def answer_question(self, question: str, retrieved_chunks: List[Dict[str, Any]], max_context_chars: int = 10000) -> Dict[str, Any]:
        # Handle case where no relevant chunks are found
        if not retrieved_chunks:
            logger.info("No relevant chunks retrieved. Returning no-information fallback.")
            return {
                "answer": "I could not find this information in the indexed repository.",
                "sources": []
            }
            
        # Build context
        context_string, used_chunks = self.build_context(retrieved_chunks, max_context_chars)
        
        if not context_string.strip():
            logger.info("Context string is empty. Returning no-information fallback.")
            return {
                "answer": "I could not find this information in the indexed repository.",
                "sources": []
            }

        prompt = self.build_prompt(question, context_string)
        
        try:
            logger.info(f"Sending prompt to Groq model {GROQ_MODEL}...")
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            answer = response.choices[0].message.content
            logger.info("Answer generated successfully.")
            
            # Format sources metadata to return
            sources = []
            for item in used_chunks:
                meta = item["metadata"]
                sources.append({
                    "relative_path": meta.get("relative_path"),
                    "start_line": meta.get("start_line"),
                    "end_line": meta.get("end_line"),
                    "symbol_name": meta.get("symbol_name"),
                    "symbol_type": meta.get("symbol_type"),
                    "language": meta.get("language"),
                    "content": item["content"],
                    "score": item.get("score", 0.0)
                })
                
            return {
                "answer": answer,
                "sources": sources
            }
            
        except BadRequestError as e:
            err_msg = str(e)
            logger.error(f"Groq BadRequestError: {err_msg}")
            if "context length" in err_msg.lower() or "reduce the length" in err_msg.lower() or "limit" in err_msg.lower():
                raise LLMError(
                    "The retrieved code context is too large for the LLM. Reduce top_k or chunk size.",
                    code="GROQ_CONTEXT_LENGTH_EXCEEDED"
                )
            else:
                raise LLMError(f"Groq API call rejected: {err_msg}", code="GROQ_BAD_REQUEST")
        except AuthenticationError as e:
            logger.error(f"Groq AuthenticationError: {str(e)}")
            raise LLMError("Groq API authentication failed. Please verify your API key.", code="GROQ_AUTH_FAILED")
        except Exception as e:
            logger.error(f"Unexpected Groq API exception: {str(e)}")
            raise LLMError(f"Failed to generate answer from Groq API: {str(e)}", code="GROQ_API_ERROR")

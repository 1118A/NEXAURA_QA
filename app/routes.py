import logging
import traceback
from flask import Blueprint, render_template, request, jsonify
from pydantic import ValidationError as PydanticValidationError
from werkzeug.exceptions import HTTPException

# Exceptions
from app.exceptions import (
    BaseAppException,
    RepositoryError,
    ParserError,
    EmbeddingError,
    VectorStoreError,
    LLMError,
    ValidationError,
)

# Schemas
from app.models.schemas import IndexRequest, AskRequest

# Services
from app.services.git_service import GitService
from app.services.file_loader_service import FileLoaderService
from app.services.parser_service import ParserService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.services.retriever_service import RetrieverService
from app.services.qa_service import QAService

from app.config import MAX_CONTEXT_CHARS

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)

# Lazy initialized services to prevent boot-time crashes on missing configs
_git_service = None
_file_loader_service = None
_parser_service = None
_embedding_service = None
_vector_store_service = None
_retriever_service = None
_qa_service = None

def get_git_service() -> GitService:
    global _git_service
    if _git_service is None:
        _git_service = GitService()
    return _git_service

def get_file_loader_service() -> FileLoaderService:
    global _file_loader_service
    if _file_loader_service is None:
        _file_loader_service = FileLoaderService()
    return _file_loader_service

def get_parser_service() -> ParserService:
    global _parser_service
    if _parser_service is None:
        _parser_service = ParserService()
    return _parser_service

def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

def get_vector_store_service() -> VectorStoreService:
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service

def get_retriever_service() -> RetrieverService:
    global _retriever_service
    if _retriever_service is None:
        _retriever_service = RetrieverService(
            get_embedding_service(),
            get_vector_store_service()
        )
    return _retriever_service

def get_qa_service() -> QAService:
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService()
    return _qa_service


# ----------------------------------------------------
# Centralized Error Handlers
# ----------------------------------------------------

@main_bp.app_errorhandler(BaseAppException)
def handle_app_exception(e: BaseAppException):
    logger.error(f"Application Error [{e.code}]: {e.message}")
    logger.error(traceback.format_exc())
    return jsonify({
        "success": False,
        "error": e.message,
        "code": e.code
    }), e.status_code

@main_bp.app_errorhandler(PydanticValidationError)
def handle_pydantic_validation_error(e: PydanticValidationError):
    # Extract the first validation message
    errors = e.errors()
    first_error = errors[0]
    msg = f"{first_error['loc'][0]}: {first_error['msg']}" if first_error['loc'] else first_error['msg']
    logger.warning(f"Request Validation Error: {msg}")
    return jsonify({
        "success": False,
        "error": msg,
        "code": "VALIDATION_ERROR"
    }), 400

@main_bp.app_errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    logger.warning(f"HTTP Exception [{e.code}]: {e.description}")
    return jsonify({
        "success": False,
        "error": e.description,
        "code": f"HTTP_ERROR_{e.code}"
    }), e.code

@main_bp.app_errorhandler(Exception)
def handle_general_exception(e: Exception):
    logger.exception("Unhandled System Exception occurred:")
    return jsonify({
        "success": False,
        "error": "A general server error occurred. Please check the logs internally.",
        "code": "INTERNAL_SERVER_ERROR"
    }), 500


# ----------------------------------------------------
# HTTP Routes
# ----------------------------------------------------

@main_bp.route("/")
def index():
    import time
    from datetime import datetime
    
    # Recommended light/dark theme based on server hour
    local_hour = time.localtime().tm_hour
    default_theme = "light" if 6 <= local_hour < 18 else "dark"
    
    # Recommended weather theme based on month using datetime
    current_month = datetime.now().month
    if current_month in [12, 1, 2]:
        default_weather = "winter"
    elif current_month in [3, 4, 5]:
        default_weather = "sunny"
    elif current_month in [6, 7, 8, 9]:
        default_weather = "rainy"
    else:
        default_weather = "cloudy"
        
    return render_template(
        "index.html",
        default_theme=default_theme,
        default_weather=default_weather
    )

@main_bp.route("/favicon.ico")
def favicon():
    import os
    from flask import send_from_directory
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), 'static', 'images'),
        'logo.jpg',
        mimetype='image/jpeg'
    )

@main_bp.route("/health", methods=["GET"])
def health():
    from app.config import CONFIG_ERRORS
    if CONFIG_ERRORS:
        return jsonify({
            "status": "unhealthy",
            "errors": CONFIG_ERRORS
        }), 503
    
    # Try verifying Chroma Cloud and Groq API
    try:
        get_vector_store_service()
        get_qa_service()
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "errors": [f"Service initialization failed: {str(e)}"]
        }), 503
        
    return jsonify({"status": "healthy"}), 200

@main_bp.route("/index", methods=["POST"])
def index_repository():
    # 1. Parse and Validate Request JSON
    data = request.get_json() or {}
    try:
        req = IndexRequest(**data)
    except PydanticValidationError as e:
        raise e
        
    repo_url = req.repo_url
    
    # Get lazy services
    git_srv = get_git_service()
    loader_srv = get_file_loader_service()
    parser_srv = get_parser_service()
    embed_srv = get_embedding_service()
    vector_srv = get_vector_store_service()
    
    logger.info(f"Starting repository indexing: {repo_url}")
    
    # 2. Clone/Update Repo
    repo_path = git_srv.clone_or_update_repo(repo_url)
    
    # 3. Scan & Load files
    code_files = loader_srv.load_code_files(repo_path)
    
    # 4. Parse AST code chunks
    chunks = parser_srv.parse_code_files(code_files)
    if not chunks:
        raise ParserError(
            "Supported files were located but no valid code chunks could be parsed.",
            code="EMPTY_CHUNKS"
        )
        
    # 5. Reset vector store index
    vector_srv.reset()
    
    # 6. Embed texts
    texts = []
    for chunk in chunks:
        text = f"File: {chunk.relative_path}\n"
        if chunk.symbol_name:
            text += f"Symbol: {chunk.symbol_name} ({chunk.symbol_type})\n"
        text += f"Language: {chunk.language}\n\n{chunk.content}"
        texts.append(text)
        
    embeddings = embed_srv.embed_texts(texts)
    
    # 7. Upsert chunks
    vector_srv.add_chunks(chunks, embeddings)
    
    logger.info(f"Indexing completed for {repo_url}. Files: {len(code_files)}, Chunks: {len(chunks)}")
    
    return jsonify({
        "success": True,
        "files_indexed": len(code_files),
        "chunks_indexed": len(chunks),
        "message": f"Successfully indexed repository with {len(code_files)} files and {len(chunks)} parsed chunks."
    }), 200

@main_bp.route("/ask", methods=["POST"])
def ask_question():
    # 1. Parse and Validate Request JSON
    data = request.get_json() or {}
    try:
        req = AskRequest(**data)
    except PydanticValidationError as e:
        raise e
        
    question = req.question
    top_k = req.top_k
    similarity_threshold = req.similarity_threshold
    
    # Get lazy services
    retriever_srv = get_retriever_service()
    qa_srv = get_qa_service()
    
    logger.info(f"Question query: '{question}' (top_k={top_k}, similarity_threshold={similarity_threshold})")
    
    # 2. Retrieve relevant chunks
    retrieved_chunks = retriever_srv.retrieve_relevant_chunks(
        query=question,
        top_k=top_k,
        similarity_threshold=similarity_threshold
    )
    
    # 3. Answer question via LLM (Groq)
    result = qa_srv.answer_question(
        question=question,
        retrieved_chunks=retrieved_chunks,
        max_context_chars=MAX_CONTEXT_CHARS
    )
    
    return jsonify({
        "success": True,
        "answer": result["answer"],
        "sources": result["sources"]
    }), 200

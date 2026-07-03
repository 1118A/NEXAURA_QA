class BaseAppException(Exception):
    """Base exception for the application."""
    def __init__(self, message: str, code: str = "INTERNAL_SERVER_ERROR", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class RepositoryError(BaseAppException):
    """Exception raised for repository git, loader, or file structure errors."""
    def __init__(self, message: str, code: str = "REPOSITORY_ERROR", status_code: int = 400):
        super().__init__(message, code, status_code)


class ParserError(BaseAppException):
    """Exception raised for AST parser or tree-sitter issues."""
    def __init__(self, message: str, code: str = "PARSER_ERROR", status_code: int = 500):
        super().__init__(message, code, status_code)


class EmbeddingError(BaseAppException):
    """Exception raised for sentence-transformer or embedding computation failures."""
    def __init__(self, message: str, code: str = "EMBEDDING_ERROR", status_code: int = 500):
        super().__init__(message, code, status_code)


class VectorStoreError(BaseAppException):
    """Exception raised for database (Chroma) failures."""
    def __init__(self, message: str, code: str = "VECTOR_STORE_ERROR", status_code: int = 500):
        super().__init__(message, code, status_code)


class LLMError(BaseAppException):
    """Exception raised for LLM (Groq) integration failures."""
    def __init__(self, message: str, code: str = "LLM_ERROR", status_code: int = 500):
        super().__init__(message, code, status_code)


class ValidationError(BaseAppException):
    """Exception raised for request validation failures."""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR", status_code: int = 400):
        super().__init__(message, code, status_code)

import logging
from pathlib import Path
from typing import List

from app.config import SUPPORTED_EXTENSIONS
from app.models.schemas import CodeFile
from app.exceptions import RepositoryError

logger = logging.getLogger(__name__)

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    ".env",
    "__pycache__",
    "node_modules",
    ".next",
    "dist",
    "build",
    "target",
    "out",
    ".idea",
    ".vscode",
}

class FileLoaderService:
    def should_ignore(self, path: Path) -> bool:
        return any(part in IGNORE_DIRS for part in path.parts)

    def load_code_files(self, repo_path: Path) -> List[CodeFile]:
        code_files = []
        
        if not repo_path.exists() or not repo_path.is_dir():
            raise RepositoryError(
                f"Repository path does not exist or is not a directory: {repo_path}",
                code="INVALID_REPOSITORY"
            )

        logger.info(f"Scanning directory {repo_path} for code files...")
        
        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue

            if self.should_ignore(file_path):
                continue

            if file_path.suffix not in SUPPORTED_EXTENSIONS:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {str(e)}")
                continue

            relative_path = str(file_path.relative_to(repo_path))
            
            # Standardize paths to use forward slashes for cross-platform consistency
            relative_path = relative_path.replace("\\", "/")

            code_files.append(
                CodeFile(
                    file_path=str(file_path).replace("\\", "/"),
                    relative_path=relative_path,
                    content=content,
                    extension=file_path.suffix,
                )
            )

        logger.info(f"Found {len(code_files)} supported code files.")
        
        if not code_files:
            raise RepositoryError(
                "No supported code files found in the repository. Supported: " + ", ".join(SUPPORTED_EXTENSIONS),
                code="NO_SUPPORTED_FILES"
            )

        return code_files

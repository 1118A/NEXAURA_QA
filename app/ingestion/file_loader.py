from pathlib import Path
from typing import List

from app.config import SUPPORTED_EXTENSIONS
from app.models.schemas import CodeFile


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
}


def should_ignore(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def load_code_files(repo_path: Path) -> List[CodeFile]:
    code_files = []

    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue

        if should_ignore(file_path):
            continue

        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        relative_path = str(file_path.relative_to(repo_path))

        code_files.append(
            CodeFile(
                file_path=str(file_path),
                relative_path=relative_path,
                content=content,
                extension=file_path.suffix,
            )
        )

    return code_files
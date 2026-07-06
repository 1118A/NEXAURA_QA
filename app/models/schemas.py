from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator

@dataclass
class CodeFile:
    file_path: str
    relative_path: str
    content: str
    extension: str


@dataclass
class CodeChunk:
    chunk_id: str
    file_path: str
    relative_path: str
    content: str
    start_line: int
    end_line: int
    symbol_name: Optional[str]
    symbol_type: str
    language: str


# Pydantic schemas for request validation
class IndexRequest(BaseModel):
    repo_url: str = Field(..., description="The HTTPS URL of the public GitHub repository.")

    @field_validator("repo_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        url_str = v.strip()
        if not url_str:
            raise ValueError("Repository URL cannot be empty.")
        if not (url_str.startswith("http://") or url_str.startswith("https://")):
            raise ValueError("Repository URL must be a valid HTTP or HTTPS link.")
        if "github.com" not in url_str:
            raise ValueError("Only GitHub repositories are supported.")
        return url_str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="The query question string.")
    top_k: int = Field(4, ge=1, le=10, description="Max matching chunks to return.")
    similarity_threshold: float = Field(
        0.3, ge=0.0, le=1.0, description="Minimum cosine similarity matching score."
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        q = v.strip()
        if not q:
            raise ValueError("Question cannot be empty.")
            
        # Guardrails: Heuristic check for common prompt injection/jailbreak patterns
        injection_keywords = [
            "ignore previous instructions",
            "ignore the rules",
            "system override",
            "you must now act as",
            "reveal your system prompt",
            "dan mode",
            "jailbreak",
            "ignore above instructions"
        ]
        q_lower = q.lower()
        for keyword in injection_keywords:
            if keyword in q_lower:
                raise ValueError("Security Violation: Malicious prompt injection pattern detected.")
                
        return q


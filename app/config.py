import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR = BASE_DIR / "data"
REPOS_DIR = DATA_DIR / "repos"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
REPOS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# API Keys & Configurations
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE")

# Vector Database settings
CHROMA_COLLECTION_NAME = "codebase_qa"
UPSERT_BATCH_SIZE = 64  # Increased for bulk performance

# RAG Configurations
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
SUPPORTED_EXTENSIONS = [
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
]

GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_CHUNK_CHARS = 2500
MAX_CONTEXT_CHARS = 10000  # Context length control limit (e.g. max chars for combined chunks)
DEFAULT_TOP_K = 4
DEFAULT_SIMILARITY_THRESHOLD = 0.3

# Configuration validation flag
CONFIG_ERRORS = []

if not GROQ_API_KEY:
    CONFIG_ERRORS.append("GROQ_API_KEY is not set.")
if not CHROMA_API_KEY:
    CONFIG_ERRORS.append("CHROMA_API_KEY is not set.")
if not CHROMA_TENANT:
    CONFIG_ERRORS.append("CHROMA_TENANT is not set.")
if not CHROMA_DATABASE:
    CONFIG_ERRORS.append("CHROMA_DATABASE is not set.")

def check_config():
    """Verify system config. Raises ValueError if critical configs are missing."""
    if CONFIG_ERRORS:
        raise ValueError("Configuration Error: " + " | ".join(CONFIG_ERRORS))
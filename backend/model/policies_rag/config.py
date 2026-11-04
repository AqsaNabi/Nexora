
import os
from pathlib import Path

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

# config.py is inside backend/model/policies_rag/
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent

# --------------------------------------------------
# POLICY DOCUMENT
# --------------------------------------------------

POLICY_DIR = BACKEND_DIR / "storage" / "policies"
POLICY_FILE = POLICY_DIR / "Policy.pdf"

# --------------------------------------------------
# OLLAMA CONFIGURATION
# --------------------------------------------------

OLLAMA_BASE_URL = "http://localhost:11434"

CHAT_MODEL = "llama3.2"
EMBEDDING_MODEL = "nomic-embed-text"

# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/nexora"
)

COLLECTION_NAME = "company_policies"

# --------------------------------------------------
# RAG CONFIGURATION
# --------------------------------------------------

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_K = 5

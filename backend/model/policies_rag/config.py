
import os
from pathlib import Path

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent

# --------------------------------------------------
# POLICY DOCUMENT
# --------------------------------------------------

POLICY_DIR = BACKEND_DIR / "storage" / "policy" #khur
POLICY_FILE = POLICY_DIR / "policy.pdf"

# --------------------------------------------------
# OLLAMA CONFIGURATION
# --------------------------------------------------

OLLAMA_BASE_URL = "http://localhost:11434"

# LLM used for answering user questions
CHAT_MODEL = "llama3.2"

# Embedding model used to convert policy text into vectors
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

# Number of relevant document chunks retrieved per question
RETRIEVER_K = 5

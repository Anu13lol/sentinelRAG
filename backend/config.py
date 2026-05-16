import os
from dotenv import load_dotenv

#Initialize environment variables
load_dotenv()

#API Keys & Endpoints
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#Veea Lobster Trap :Security Layer & Prompt Firewall
LOBSTER_TRAP_API_KEY = os.getenv("LOBSTER_TRAP_API_KEY")
LOBSTER_TRAP_ENDPOINT = "http://localhost:8080" #localhost

#LOBSTER_TRAP_ENDPOINT = os.getenv("LOBSTER_TRAP_ENDPOINT")

#Storage Config
#SQLite for local dev speed and zero-config dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentinelrag.db")

#Path for vector database
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vector_store")

#RAG/Data Ingestion Hyperparameters
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
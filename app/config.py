import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
   # --- EMBEDDINGS ---
   GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
   HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API")

   # --- VECTOR DB (QDRANT) ---
   QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
   QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
   QDRANT_COLLECTION = "GenAIProject"

   # --- REASONING ENGINE (GROQ) ---
   GROQ_API_KEY = os.getenv("GROQ_API_KEY")
   GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
   GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")

   # --- OBSERVABILITY ---
   LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
   LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
   LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "rag_scale_test")
   LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

settings = Settings()
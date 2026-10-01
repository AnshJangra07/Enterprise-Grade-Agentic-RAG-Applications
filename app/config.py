import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
   # --- GEMINI EMBEDDINGS ---
   GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

   # --- VECTOR DB (QDRANT) ---
   QDRANT_URL = os.getenv("QDRANT_CLUSTER_ENDPOINT")
   QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
   QDRANT_COLLECTION = "GenAIProject"

   # --- REASONING ENGINE (GROQ) ---
   GROQ_API_KEY = os.getenv("GROQ_API_KEY")
   GROQ_MODEL = "llama-3.3-70b-versatile"
   GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")

settings = Settings()
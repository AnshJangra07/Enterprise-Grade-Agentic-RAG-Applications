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
   GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
   GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")

   
   # --- LLM GATEWAY (PORTKEY) ---
   PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
   GATEWAY_CONFIG = os.getenv("PORTKEY_GATEWAY_CONFIG")
   GROQ_SLUG = os.getenv("GROQ_SLUG", "groq")
   GROQ_SLUG_2 = os.getenv("GROQ_SLUG_2", "groq")

   # --- OBSERVABILITY ---
   LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
   LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
   LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "rag_scale_test")
   LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")



# Apply LangChain environment variables for automatic tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGSMITH_TRACING", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "rag_scale_test")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")


settings = Settings()
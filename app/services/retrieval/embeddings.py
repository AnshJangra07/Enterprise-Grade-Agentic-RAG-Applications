import time
import logfire
# from langchain_google_genai import GoogleGenerativeAIEmbeddings # If you wanna use this , you can 
from langchain_huggingface import HuggingFaceEmbeddings           # I prefer this just bcoz it's free
from app.config import settings


BATCH_SIZE = 50
_GEMINI_DIM = 3072
_FALLBACK_DIM = 768

_active_model = None
_model_type: str | None = None

def _probe_gemini():
   """Try one embed call to verify Gemini is reachable. Return model or None"""


def _load_fallback():
   return

def __init():
   return

def get_embedding_dim() -> int:
   "Return the vector dimension for the active model. Call after _init()."
   return

def _embed_batch(batch: list(str))->list[list[str]]:
   return

def embed_query(query: str)->list[float]:
   return

def embed_texts(texts: list(str))->list[list[float]]:
   return
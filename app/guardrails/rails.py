import re

import logfire
from langchain_groq import ChatGroq
from nemoguardrails import RailsConfig, LLMRails
from nemoguardrails.integrations.langchain.llm_adapter import LangChainLLMAdapter

from app.config import settings
from app.guardrails.colang_rules import COLANG_CONTENT, YAML_CONTENT, RAIL_INDICATORS


OFFTOPIC_PATTERNS = (
    "tell me a joke",
    "what is the weather",
    "what is 2 plus 2",
    "what is 2+2",
    "who won the game",
    "recommend a movie",
    "capital of france",
    "what should i eat",
    "restaurant near me",
    "math homework",
    "history",
    "poem",
    "movie",
    "weather today",
    "good restaurant",
)


_rails: LLMRails | None = None


def _normalize_message(message: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", message.lower()).strip()


def is_off_topic(message: str) -> bool:
    normalized = _normalize_message(message)
    if not normalized:
        return False
    return any(pattern in normalized for pattern in OFFTOPIC_PATTERNS)


def initialize_rails() -> None:
    """
    Build the NeMo LLMRails singleton at app startup.
    Use the configured Groq model so the guardrail layer stays in sync with the
    rest of the application instead of depending on a stale hardcoded alias.
    """
    global _rails

    model_name = settings.GROQ_MODEL or "openai/gpt-oss-120b"

    guard_llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=model_name,
        temperature=0
    )

    config = RailsConfig.from_content(
        colang_content=COLANG_CONTENT,
        yaml_content=YAML_CONTENT or None
    )

    _rails = LLMRails(config, llm=LangChainLLMAdapter(guard_llm))
    logfire.info(f"NeMo Guardrails initialised ({model_name}).")
    
    


def guard(message: str) -> tuple[bool, str | None]:
    """
    Run a user message through the NeMo rails gate.

    Returns:
        (True,  rail_response) — a rail fired; return this response immediately,
                                skip the RAG pipeline entirely.
        (False, None)          — message is clean; proceed to LangGraph.
    """
    if is_off_topic(message):
        logfire.info(f"Guardrails fired | off-topic query='{message[:80]}'")
        return True, (
            "I'm an Enterprise IT Assistant focused on Kubernetes, Intel hardware, "
            "and networking. I can't help with that — but ask me anything technical!"
        )

    if _rails is None:
        logfire.warning("Guardrails not initialised — skipping gate.")
        return False, None

    with logfire.span("Guardrails Check"):
        result = _rails.generate(messages=[{"role": "user", "content": message}])

        # NeMo returns {'role': 'assistant', 'content': '...'} — extract text
        content = result.get("content", "") if isinstance(result, dict) else str(result)

        fired = any(indicator in content for indicator in RAIL_INDICATORS)

        if fired:
            logfire.info(f"Guardrails fired | query='{message[:80]}'")
            return True, content

        logfire.info("Guardrails passed.")
        return False, None

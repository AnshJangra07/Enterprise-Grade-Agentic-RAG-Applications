import logfire
from langchain_groq import ChatGroq
from nemoguardrails import RailsConfig, LLMRails

from app.config import settings
from app.guardrails.colang_rules import COLANG_CONTENT, YAML_CONTENT, RAIL_INDICATORS


_rails: LLMRails | None = None


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
        yaml_content=YAML_CONTENT
    )

    _rails = LLMRails(config, llm=guard_llm)
    logfire.info(f"NeMo Guardrails initialised ({model_name}).")
    
    


def guard(message: str) -> tuple[bool, str | None]:
    """
    Run a user message through the NeMo rails gate.

    Returns:
        (True,  rail_response) — a rail fired; return this response immediately,
                                skip the RAG pipeline entirely.
        (False, None)          — message is clean; proceed to LangGraph.
    """
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

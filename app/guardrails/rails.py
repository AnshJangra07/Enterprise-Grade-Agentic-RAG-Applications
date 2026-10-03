import logfire
from nemoguardrails import RailsConfig, LLMRails
from nemoguardrails.integrations.langchain.llm_adapter import LangChainLLMAdapter

from app.config import settings
from app.gateway import get_langchain_llm
from app.guardrails.colang_rules import COLANG_CONTENT, YAML_CONTENT, RAIL_INDICATORS


_rails: LLMRails | None = None


def _is_guardrail_fired(content: str) -> bool:
    lower = content.lower()
    if any(indicator.lower() in lower for indicator in RAIL_INDICATORS):
        return True
    return any(
        phrase in lower for phrase in (
            "i can't help with that",
            "i cannot help with that",
            "i maintain consistent guidelines",
            "i am here to help with kubernetes",
        )
    )


def initialize_rails() -> None:
    """
    Build the NeMo LLMRails singleton at app startup.
    Use the Portkey-backed LLM so guardrails share the same gateway path as the rest of the app.
    """
    global _rails

    model_name = settings.GROQ_MODEL or "openai/gpt-oss-120b"
    guard_llm = get_langchain_llm(feature="guardrails")

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
    if _rails is None:
        logfire.warning("Guardrails not initialised — skipping gate.")
        return False, None

    with logfire.span("Guardrails Check"):
        result = _rails.generate(messages=[{"role": "user", "content": message}])

        content = result.get("content", "") if isinstance(result, dict) else str(result)
        fired = _is_guardrail_fired(content)

        if fired:
            logfire.info(f"Guardrails fired | query='{message[:80]}'")
            return True, content

        logfire.info("Guardrails passed.")
        return False, None

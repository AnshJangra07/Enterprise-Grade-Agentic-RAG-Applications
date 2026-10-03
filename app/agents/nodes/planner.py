import re

from app.agents.state import AgentState
from app.config import settings
from app.gateway import get_langchain_llm
import logfire

# Portkey-backed LLM: fallback + cache + retry — same .invoke() interface as ChatGroq
llm = get_langchain_llm(feature="planner")


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
    "write me a poem",
    "good restaurant",
    "what is the best restaurant",
)

GREETINGS = ("hi", "hello", "hey", "hey there", "good morning", "good afternoon", "good evening")


def _normalize_message(message: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", message.lower()).strip()


def _is_greeting(message: str) -> bool:
    normalized = _normalize_message(message)
    return any(greeting in normalized for greeting in GREETINGS)


def _is_off_topic(message: str) -> bool:
    normalized = _normalize_message(message)
    if not normalized:
        return False
    return any(pattern in normalized for pattern in OFFTOPIC_PATTERNS)


def planner_node(state: AgentState):
   """
   The Planner determined if a 
   search is needed based on the Entire conversation
   """


   # Get the conversation history(excluding the latest message)
   history = ""
   for msg in state["messages"][:-1]:
      role = "User" if msg["role"] == "user" else "Assistent"
      history += f"{role}: {msg['content']}\n"


   user_message = state["messages"][-1]["content"] if state["messages"] else ""
   normalized = _normalize_message(user_message)

   if _is_greeting(normalized):
      return {
         "current_query": "CONVERSATIONAL",
         "status": "Handling conversationally (using memory)...",
         "plan": ["Intent: Conversational/Memory", "Retrieval: Skipped"]
      }

   if _is_off_topic(normalized):
      return {
         "current_query": "OFFTOPIC",
         "status": "Off-topic request — blocked before retrieval.",
         "plan": ["Intent: Guardrail Block", "Retrieval: Skipped"]
      }

   prompt = f"""
   You are an intelligent Assistant Planner. 
   Analyze the conversation history and the latest user message.
   
   CONVERSATION HISTORY:
   {history}
   
   LATEST MESSAGE:
   "{user_message}"
   
   Task:
   1. If the latest message is a greeting (hi, hello) or a question that can be answered using ONLY the conversation history above (e.g., "what is my name"), respond with 'CONVERSATIONAL'.
   2. If it is a technical question about Kubernetes, Intel, or Networking that requires fresh documentation, output a refined search query.
   3. If it is unrelated to the supported technical scope, return 'OFFTOPIC'.
   
   Output ONLY 'CONVERSATIONAL', 'OFFTOPIC', or the search query.
   """


   with logfire.span("Planner Decision"):
      decision = llm.invoke(prompt).content.strip()
      logfire.info(f"Intent identified: {decision}")
   
   if decision == "CONVERSATIONAL":
      return {
         "current_query": "CONVERSATIONAL",
         "status": "Handling conversationally (using memory)...",
         "plan": ["Intent: Conversational/Memory", "Retrieval: Skipped"]
      }

   if decision == "OFFTOPIC":
      return {
         "current_query": "OFFTOPIC",
         "status": "Off-topic request — blocked before retrieval.",
         "plan": ["Intent: Guardrail Block", "Retrieval: Skipped"]
      }
   
   return {
      "current_query": decision,
      "status": f"Technical research needed. Searching for: {decision}",
      "plan": ["Intent: Technical", f"Search Term: {decision}"]
   }
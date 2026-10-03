import json

from app.agents.state import AgentState
from app.config import settings
from app.gateway import get_langchain_llm
import logfire

# Portkey-backed LLM: fallback + cache + retry — same .invoke() interface as ChatGroq
llm = get_langchain_llm(feature="planner")


def parse_planner_decision(raw_decision: str):
   """Normalize the planner output into a stable JSON-like structure."""
   text = (raw_decision or "").strip()
   if text.startswith("```"):
      text = text.strip("`")
      if text.lower().startswith("json"):
         text = text[4:].strip()

   try:
      parsed = json.loads(text)
      if isinstance(parsed, dict):
         intent = str(parsed.get("intent", "")).upper()
         search_query = parsed.get("search_query")
         if intent in {"CONVERSATIONAL", "OFFTOPIC", "TECHNICAL"}:
            return {"intent": intent, "search_query": search_query}
   except json.JSONDecodeError:
      pass

   normalized = text.strip().upper()
   if normalized in {"CONVERSATIONAL", "OFFTOPIC"}:
      return {"intent": normalized, "search_query": None}

   return {"intent": "TECHNICAL", "search_query": text.strip() or None}


def planner_node(state: AgentState):
   """
   The Planner determines whether the request is conversational,
   technical, or out of the supported enterprise IT scope.
   """

   history = ""
   for msg in state["messages"][:-1]:
      role = "User" if msg["role"] == "user" else "Assistent"
      history += f"{role}: {msg['content']}\n"

   user_message = state["messages"][-1]["content"] if state["messages"] else ""

   prompt = f"""
   You are an intelligent Assistant Planner.
   Analyze the conversation history and the latest user message.

   CONVERSATION HISTORY:
   {history}

   LATEST MESSAGE:
   "{user_message}"

   Task:
   Return valid JSON only with this schema:
   {{
     "intent": "CONVERSATIONAL" | "OFFTOPIC" | "TECHNICAL",
     "search_query": "refined technical query or null"
   }}

   Rules:
   1. If the latest message is a greeting or can be answered using ONLY the conversation history above, return {{"intent": "CONVERSATIONAL", "search_query": null}}.
   2. If the latest message is about Kubernetes, Intel hardware, or enterprise networking and requires fresh documentation, return {{"intent": "TECHNICAL", "search_query": "...refined query..."}}.
   3. If the latest message is unrelated to the supported technical scope, return {{"intent": "OFFTOPIC", "search_query": null}}.

   Return only valid JSON, no explanation and no Markdown code fences.
   """

   with logfire.span("Planner Decision"):
      raw_decision = llm.invoke(prompt).content.strip()
      parsed = parse_planner_decision(raw_decision)
      logfire.info(f"Intent identified: {parsed}")

   decision = parsed["intent"]
   search_query = parsed["search_query"]

   if decision == "CONVERSATIONAL":
      return {
         "intent": "CONVERSATIONAL",
         "current_query": "CONVERSATIONAL",
         "status": "Handling conversationally (using memory)...",
         "plan": ["Intent: Conversational/Memory", "Retrieval: Skipped"]
      }

   if decision == "OFFTOPIC":
      return {
         "intent": "OFFTOPIC",
         "current_query": "OFFTOPIC",
         "status": "Off-topic request — blocked before retrieval.",
         "plan": ["Intent: Off-topic", "Retrieval: Skipped"]
      }

   technical_query = search_query or user_message
   return {
      "intent": "TECHNICAL",
      "current_query": technical_query,
      "status": f"Technical research needed. Searching for: {technical_query}",
      "plan": ["Intent: Technical", f"Search Term: {technical_query}"]
   }
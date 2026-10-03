# Critical : logfire MUST be configures before ALL other imports so that spans from all modules are captured from the start.

import os

import logfire
from dotenv import load_dotenv
from fastapi import FastAPI, Response, HTTPException

load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))


# Now safe to import app modules - logfire is already active
from pydantic import BaseModel
from typing import Optional

from app.agents.graph import rag_agent
from app.guardrails import initialize_rails, guard


app = FastAPI(title="Enterprise Agentic RAG API")


@app.on_event("startup")
def startup_event():
   initialize_rails()


class QueryRequest(BaseModel):
   q : str
   thread_id : Optional[str] = "default_user"


@app.get("/")
def home():
   return {"message": "Enterprise LangGraph RAG API is live."}


@app.get("/graph")
def get_graph_image():
   """
   Returns the Mermaid image of the agent's workflow.
   """
   try:
      png_butes = rag_agent.get_graph().draw_mermaid_png()
      return Response(content=png_butes, media_type="image/png")
   except Exception as e :
      return {"error": f"Could not generate graph : {e}"}


@app.post("/query")
def query(request: QueryRequest):
   """
   Executes the LangGraph RAG workflow with memory using Post request.
   """
   q = request.q
   thread_id = request.thread_id

   intial_state = {
      "messages": [{"role": "user", "content": q}],
      "intent": "UNKNOWN",
      "current_query": q,
      "documents": [],
      "plan": ["Start"],
      "status": "Intializing Graph...",
      "final_answer": "",
   }

   config = {"configurable": {"thread_id": thread_id}}

   try:
      rail_fired, rail_response = guard(q)
      if rail_fired:
         logfire.info(f"Request block by guardrails , thread = {thread_id}")
         return {
            "question": q,
            "answer": rail_response,
            "thought_process": ["Intent: Guardrails Fired", "Retrieval: Skipped"],
            "status": "Blocked by guardrails",
            "sources": [],
         }

      final_output = rag_agent.invoke(intial_state, config=config)

      return {
         "question": q,
         "answer": final_output.get("final_answer"),
         "thought_process": final_output.get("plan"),
         "status": final_output.get("status"),
         "sources": final_output.get("documents", []),
      }
   except Exception as e:
      logfire.error("Backend execution failed", error=str(e))
      raise HTTPException(status_code=500, detail="Internal server error") from e
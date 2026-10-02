# Critical : logfire MUST be configures before ALL other imports so that spans from all modules are captured from the start.

import logfire
import os
from dotenv import load_dotenv

load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))



# Now safe to import app modules - logfire is already active
from fastapi import FastAPI, Response
from app.agents.graph import rag_agent

from pydantic import BaseModel
from typing import Optional


app = FastAPI(title="Enterprise Agentic RAG API")


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
   Executes the LangGraph workflow with memory using Post request.
   """
   q = request.q
   thread_id = request.thread_id

   intial_state = {
      "messages" : [{"role":"user", "content":q}],
      "current_query" : q,
      "documents": [],
      "plan": ["Start"],
      "status": "Intializing Graph..."
   }

   # Configuration for memory - thread_id
   config = {"configurable":{"thread_id":thread_id}}

   try:
      final_output = rag_agent.invoke(intial_state,config=config)

      return {
         "question":q,
         "answer":final_output.get("final_answer"),
         "thought_process": final_output.get("plan"),
         "status":final_output.get("status"),
         "sources": final_output.get("documents",[])
      }
   except Exception as e:
      logfire.info(f"Backend Execution failed: {e}")
      return {
         "question":q,
         "answer":"I apologize, but I encountered an internal error while processing",
         "thought_process": ["Error encountered during execution"],
         "status":"error",
         "sources": []
      }
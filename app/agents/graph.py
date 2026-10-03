from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import AgentState
from app.agents.nodes.planner import planner_node
from app.agents.nodes.retriever import retriever_node
from app.agents.nodes.responder import generate_node
from app.agents.nodes.off_topic_node import off_topic_node



workflow = StateGraph(AgentState)


workflow.add_node("planner", planner_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("responder", generate_node)
workflow.add_node("offtopic", off_topic_node)


def router_planner(state: AgentState):
   """
   Routes the workflow based on the planner's decision.
   """
   intent = state.get("intent") or state.get("current_query")
   if intent == "CONVERSATIONAL":
      return "responder"
   if intent == "OFFTOPIC":
      return "offtopic"
   return "retriever"

workflow.set_entry_point("planner")


workflow.add_conditional_edges(
   "planner",
   router_planner,
   {
      "retriever": "retriever",
      "responder": "responder",
      "offtopic": "offtopic",
   }
)


workflow.add_edge("retriever", "responder")
workflow.add_edge("responder", END)
workflow.add_edge("offtopic", END)


# MEMORY UPGRADE
# MemorySaver allows the agent to remember conversations based on 'thread_id'
checkpointer = MemorySaver()


# Compile
rag_agent = workflow.compile(checkpointer=checkpointer)
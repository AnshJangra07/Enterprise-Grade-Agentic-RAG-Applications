from app.agents.state import AgentState

def off_topic_node(state: AgentState):
   content = (
      "I'm an Enterprise IT Assistant focused on Kubernetes, Intel hardware, "
      "and enterprise networking. I can't help with that, but ask me a technical question!"
   )
   return {
      "intent": "OFFTOPIC",
      "final_answer": content,
      "status": "Blocked as off-topic.",
      "plan": state.get("plan", []) + ["Intent: Off-topic", "Retrieval: Skipped"],
      "documents": [],
      "messages": [{"role": "assistant", "content": content}],
   }
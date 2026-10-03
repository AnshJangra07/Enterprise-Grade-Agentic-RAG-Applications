import logfire
from app.agents.state import AgentState
from app.gateway import portkey_client, extract_cache_status



def generate_node(state: AgentState):
   """
   Synthesizes a response using both documentation context and conversation history.
   Uses the native Portkey client (not LangChain) so we can read the
   x-portkey-cache-status response header and surface Cache: Hit in the UI.
   """

   query = state.get("current_query")
   intent = state.get("intent")

   if intent == "OFFTOPIC" or query == "OFFTOPIC":
      content = (
         "I'm an Enterprise IT Assistant focused on Kubernetes, Intel hardware, "
         "and enterprise networking. I can't help with that, but ask me a technical question!"
      )
      return {
         "final_answer": content,
         "status": "Blocked as off-topic.",
         "plan": state.get("plan", []) + ["Intent: Off-topic", "Retrieval: Skipped"],
         "documents": [],
         "messages": [{"role": "assistant", "content": content}],
      }

   history_str = ""
   for msg in state["messages"][:-1]:
      role = "User" if msg["role"] == "user" else "Assistent"
      history_str += f"{role}: {msg['content']}\n"

   user_msg = state["messages"][-1]["content"] if state["messages"] else ""

   if query == "CONVERSATIONAL" or intent == "CONVERSATIONAL":
      logfire.info("Generating conversational response using memory.")
      prompt = f"""
      You are an Enterprise AI Assistant specializing in Kubernetes,
      Intel hardware, and enterprise networking.

      You may answer general conversational questions only when they are directly
      supported by the conversation history. For unsupported requests, politely refuse
      and redirect to enterprise IT topics.

      CONVERSATION HISTORY:
      {history_str}

      LATEST MESSAGE:
      "{user_msg}"
      """
   else:
      logfire.info("Generating technical RAG response.")
      max_context_chars = 25000
      full_context = ""

      for doc in state.get("documents", []):
         if len(full_context) + len(doc) < max_context_chars:
               full_context += doc + "\n\n"
         else:
               logfire.warning("Context truncated to fit Groq TPM limits.")
               break

      prompt = f"""
      You are an Enterprise AI Assistant specializing in Kubernetes, Intel hardware,
      and enterprise networking.

      Answer the user's question using only the TECHNICAL CONTEXT provided below.
      If the request is outside these domains, politely refuse and redirect back to
      enterprise IT questions.

      TECHNICAL CONTEXT:
      {full_context}

      CONVERSATION HISTORY:
      {history_str}

      USER QUESTION:
      "{user_msg}"
      """

   with logfire.span("LLM Synthesis"):
      try:
         response = portkey_client.chat.completions.create(
            messages=[{"role":"user","content":prompt}],
            temperature=0.1
         )
         content = response.choices[0].message.content
         cache_status = extract_cache_status(response)
         is_cache_hit = cache_status == "HIT"

         if is_cache_hit:
            logfire.info("Gateway Cache Hit — response served from Portkey cache.")
            plan_update = state["plan"] + ["Cache : HIT"]
            status = "Cache hit -instant response"
         else:
            logfire.info("Response synthesised via LLM")
            plan_update = state["plan"]
            status = "Response generated."

         return {
            "final_answer": content,
            "status": status,
            "plan": plan_update,
            "documents": state.get("documents", []),
            "messages": [{"role": "assistant", "content": content}],
         }

      except Exception as e:
         logfire.error("LLM Generation failed", error=str(e))
         raise e
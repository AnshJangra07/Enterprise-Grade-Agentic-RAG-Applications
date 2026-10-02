import logfire
from app.agents.state import AgentState
from app.services.retrieval.qdrant_service import search_enterprise_knowledge
from app.services.retrieval.ranking_service import rerank_documents



def retriever_node(state: AgentState):
   """
   Performs vector search and semantic reranking for tecnical queries.
   """
   query = state["current_query"]

   with logfire.span("Knowledge Retrieval"):
      logfire.info(f"Searching Qdrant for {query}")
      raw_results = search_enterprise_knowledge(query, limit=15)
      logfire.info(f"Retrieved {len(raw_results)} condidates from Vector DB")

      doc_contents = [doc['content'] for doc in raw_results]

      with logfire.span("Semantic Reranking"):
         reranked_content = rerank_documents(query, doc_contents, top_n=5)
         logfire.info("Reranking Complete. Kept top 5 most relevant chunks")

      formatted_docs = [f"CONTENT: {doc}" for doc in rerank_documents]

   return {
      "documents" : formatted_docs,
      "status": f"Found technical content.",
      "plan" : state["plan"] + ["Context Retrieved"]
   }
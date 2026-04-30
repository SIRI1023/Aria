from langchain_core.tools import tool
from app.rag.retrieval import retrieve_context


@tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for information relevant to the query.
    Use this whenever the user asks about uploaded documents or company information."""
    context, citations = retrieve_context(query)
    if not context:
        return "No relevant information found in the knowledge base for this query."
    citation_str = ", ".join(f"{c['filename']} (page {c['page']})" for c in citations)
    return f"Sources: {citation_str}\n\n{context}"


@tool
def calculate(expression: str) -> str:
    """Evaluate a simple math expression like '2 + 2' or '100 * 0.15'.
    Only use for arithmetic calculations."""
    try:
        allowed = set("0123456789+-*/()., ")
        if not all(c in allowed for c in expression):
            return "Error: only basic arithmetic is supported."
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


TOOLS = [search_knowledge_base, calculate]

import json
from google import genai
from ..config import GEMINI_API_KEY

eval_client = genai.Client(
    api_key = GEMINI_API_KEY
)

def compute_relevance(query: str, chunks: list[dict]) -> dict:
    # Evaluates if the chunks are actually useful for the query
    if not query or not chunks:
        return {"score": 0.0, "reasoning": "Missing query or context chunks."}
    #context for evaluator
    context = "\n".join([f"[{i}] {c['text']}" for i, c in enumerate(chunks)])

    prompt = f"""
    You are a RAG Quality Auditor.
    Evaluate the relevance of the provided Context Chunks to the User Query.
    
    Criteria:
    1. Does the context contain the information needed to answer the query?
    2. Is the context direct or just tangentially related?
    
    User Query: {query}
    
    Context Chunks:
    {context}
    
    Return a valid JSON object:
    {{
        "relevance_score": float,  // 0.0 (useless) to 1.0 (perfect)
        "reasoning": "string"
    }}
    """

    try:
        response = eval_client.models.generate_content(
            model = "gemini-2.5-flash-lite",
            contents = prompt,
            config = {
                "response_mime_type": "application/json",
                "temperature": 0.0
            }
        )

        result = json.loads(response.text)
        return {
            "score": float(result.get("relevance_score", 0.0)),
            "reasoning": result.get("reasoning", "No reasoning provided."),
        }

    except Exception as e:
        return {"score": 0.0, "reasoning": f"Eval Error: {str(e)}"}
        #Fallback if AI eval fails, we could return a normalized
        #average of the retriever's distance scores.
import json
from google import genai
from ..config import GEMINI_API_KEY

eval_client = genai.Client(
    api_key=GEMINI_API_KEY
)

def compute_faithfulness(answer: str, chunks: list[dict]) -> dict:
    if not answer or not chunks:
        return {"score": 0.0, "reasoning": "Missing answer or context chunks."}
    
    context = "\n".join(c['text'] for c in chunks) #combine the chunks into a single context block

    prompt = f"""
    You are an expert RAG evaluator. 
    Analyze the provided Answer against the Context.
    
    Step 1: Extract all factual claims made in the Answer.
    Step 2: For each claim, check if it can be directly inferred from the Context.
    Step 3: Calculate the faithfulness score: (Supported Claims / Total Claims).
    
    Return a valid JSON object with this exact schema:
    {{
        "total_claims": int,
        "supported_claims": int,
        "score": float
    }}
    
    Context:
    {context}
    
    Answer:
    {answer}
    """

    try:
        response = eval_client.models.generate_content(
            model = "gemini-2.5-flash-lite",
            contents = prompt,
            config = {
                "response_mime_type": "application/json",
                "temperature": 0.0 #Deterministic evaluation
            }
        )

        result = json.loads(response.text)

        # Division by zero or hallucinated JSON rejection
        if result.get("total_claims", 0) == 0:
            return {"score": 0.0, "reasoning": "No factual claims parsed from the answer."}

        return {
            "score": float(result.get("score", 0.0)),
            "reasoning": result.get("reasoning", "No reasoning provided."),
        }

    except Exception as e:
        print(f"FAITHFULNESS ERROR: {str(e)}")
        return {"score": 0.0, "reasoning": f"Eval error: {str(e)}"}
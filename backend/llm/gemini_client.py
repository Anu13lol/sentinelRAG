from google import genai
from ..config import GEMINI_API_KEY

# Point client to proxy's endpoint
client = genai.Client(
    api_key=GEMINI_API_KEY
)

def build_prompt(query: str, chunks: list[dict]) -> str:
    context_block = ""
    for i, chunk in enumerate(chunks):
        context_block += f"[{i+1}] {chunk['text']} (Source: {chunk['source']})\n"

    return f"""
You are an enterprise document intelligence assistant (SentinelRAG).
Answer the user's question ONLY based on the provided context.
If the answer is not in the context, say 'I cannot find this in the provided documents.'
Do not use outside knowledge.

Context:
{context_block}

Question: {query}

Answer:
""".strip()

def get_gemini_response(prompt: str) -> dict:
    try:
        response = client.models.generate_content(
            model = "gemini-2.5-flash",
            contents=prompt
        )
        return {
            "answer": response.text,
            "model": "gemini-2.5-flash",
            "prompt_used": prompt,
            "finish_reason": "STOP",
        }

    except Exception as e:
        print(f"GEMINI ERROR: {str(e)}")
        return {
            "answer": f"SDK Error: {str(e)}",
            "model": "gemini-2.5-flash",
            "prompt_used": prompt,
            "finish_reason": "error",
        }

def ask(query: str, chunks: list[dict]) -> dict:
    prompt = build_prompt(query, chunks)
    return get_gemini_response(prompt)
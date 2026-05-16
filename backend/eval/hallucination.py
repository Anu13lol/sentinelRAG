import re
import json
from google import genai
from ..config import GEMINI_API_KEY

# Use Flash-Lite for the Deep Path (Semantic Check)
eval_client = genai.Client(
    api_key=GEMINI_API_KEY
)

def _heuristic_check(answer: str, chunks: list[dict], faithfulness_score: float) -> tuple[bool, str]:
    """
    Fast, deterministic check for numeric mismatches and low faithfulness.
    Returns: (is_hallucination, reasoning)
    """
    #Critical Faithfulness Check
    if faithfulness_score < 0.3:
        return True, "Critically low faithfulness score (< 0.3)."

    #Honest Refusal Check
    refusal_patterns = [
        "i cannot find", "i could not find", "not mentioned in the context",
        "no information provided", "i am sorry, but"
    ]
    if any(pattern in answer.lower() for pattern in refusal_patterns):
        return False, "Model correctly identified missing information."

    #Numeric/Date Mismatch (Regex)
    data_pattern = r'\b\d+(?:[./-]\d+)*\b'
    answer_data = set(re.findall(data_pattern, answer))
    all_chunk_text = " ".join([c['text'] for c in chunks])
    chunk_data = set(re.findall(data_pattern, all_chunk_text))

    for item in answer_data:
        # Filter out single digits to avoid false positives from list numbers
        if len(item) > 1 and item not in chunk_data:
            return True, f"Hard data mismatch: '{item}' found in answer but not in source."

    return False, ""

def _llm_check(answer: str, chunks: list[dict]) -> dict:
    """
    Deep path using Gemini 3.1 Flash-Lite to catch semantic lies.
    """
    context = "\n".join([c['text'] for c in chunks])
    prompt = f"""
    You are a Fact-Checker. Compare the Answer against the Context.
    Does the Answer contain any information that is NOT present in or 
    directly contradicted by the Context?
    
    Return a valid JSON:
    {{
        "is_hallucination": bool,
        "reasoning": "string"
    }}
    
    Context: {context}
    Answer: {answer}
    """

    try:
        response = eval_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={"response_mime_type": "application/json", "temperature": 0.0}
        )
        result = json.loads(response.text)
        return {
            "is_hallucination": bool(result.get("is_hallucination", False)),
            "reasoning": result.get("reasoning", "No semantic hallucination detected.")
        }
    except Exception as e:
        return {"is_hallucination": False, "reasoning": f"LLM Check failed: {str(e)}"}

def detect_hallucination(answer: str, chunks: list[dict], faithfulness_score: float) -> dict:
    """
    Orchestrates the two-stage hallucination detection pipeline.
    """
    #1: HEURISTICS (Fast & Free)
    h_flag, h_reasoning = _heuristic_check(answer, chunks, faithfulness_score)
    
    if h_flag:
        return {
            "is_hallucination": True,
            "reasoning": h_reasoning,
            "method": "heuristic"
        }

    #2: LLM JUDGE (Deep & Semantic)
    # Only called if the heuristic check passes.
    llm_result = _llm_check(answer, chunks)
    llm_result["method"] = "llm_judge"
    
    return llm_result
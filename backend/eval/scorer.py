from .faithfulness import compute_faithfulness
from .relevance import compute_relevance
from .hallucination import detect_hallucination

def run_eval(query: str, answer: str, chunks: list[dict]) -> dict:
    """
    The Master Scorer: Aggregates metrics into a single confidence score.
    Implements a hard cap at 0.3 if a hallucination is detected.
    """
    #Fetch individual metrics
    f_result = compute_faithfulness(answer, chunks)
    r_result = compute_relevance(query, chunks)
    
    f_score = f_result['score']
    r_score = r_result['score']
    
    #Check for Hallucination
    #uses the f_score as a fast-path trigger for the heuristic check
    h_result = detect_hallucination(answer, chunks, f_score)
    is_hallucinating = h_result['is_hallucination']
    
    #Compute Weighted Confidence Score
    # => Faithfulness (60%) + Relevance (40%)
    confidence_score = (f_score * 0.6) + (r_score * 0.4)
    
    #Hallucination Penalty (Hard Cap)
    if is_hallucinating:
        confidence_score = min(confidence_score, 0.3)
        eval_summary = "FAIL"
    elif confidence_score > 0.7:
        eval_summary = "PASS"
    elif confidence_score >= 0.4:
        eval_summary = "WARN"
    else:
        eval_summary = "FAIL"

    #Final Response Dict
    return {
        "faithfulness_score": round(f_score, 2),
        "relevance_score": round(r_score, 2),
        "relevance_reasoning": r_result.get('reasoning', ""),
        "hallucination_flag": is_hallucinating,
        "hallucination_reasoning": h_result.get('reasoning', ""),
        "hallucination_method": h_result.get('method', "unknown"),
        "confidence_score": round(confidence_score, 2),
        "eval_summary": eval_summary
    }
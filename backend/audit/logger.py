import json
from datetime import datetime
from ..database.db import SessionLocal
from ..database.models import QueryLog, EvalResult

def log_query(db, query_text: str, answer_text: str, was_blocked: bool):
    """creates a basic query record."""
    new_log = QueryLog(
        query_text=query_text,
        answer_text=answer_text,
        was_blocked=was_blocked
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def log_eval(db, query_log_id: int, eval_result: dict, chunks: list):
    """Logs the full evaluation suite results."""
    #combine reasonings into one searchable block
    combined_reasoning = (
        f"Relevance: {eval_result.get('relevance_reasoning', '')} | "
        f"Hallucination: {eval_result.get('hallucination_reasoning', '')}"
    )
    
    new_eval = EvalResult(
        query_log_id=query_log_id,
        faithfulness_score=eval_result['faithfulness_score'],
        relevance_score=eval_result['relevance_score'],
        hallucination_flag=eval_result['hallucination_flag'],
        confidence_score=eval_result['confidence_score'],
        eval_summary=eval_result['eval_summary'],
        source_chunks=json.dumps([c['text'] for c in chunks]),
        reasoning_log=combined_reasoning
    )
    db.add(new_eval)
    db.commit()
    db.refresh(new_eval)
    return new_eval

def get_audit_logs(db, limit=50):
    """Fetches joined logs for the admin dashboard."""
    logs = db.query(QueryLog).order_by(QueryLog.created_at.desc()).limit(limit).all()
    
    output = []
    for log in logs:
        eval_data = log.evaluation
        output.append({
            "id": log.id,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "query": log.query_text,
            "answer": log.answer_text,
            "status": eval_data.eval_summary if eval_data else "PENDING",
            "confidence": eval_data.confidence_score if eval_data else 0.0,
            "hallucination": eval_data.hallucination_flag if eval_data else False
        })
    return output
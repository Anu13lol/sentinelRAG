from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.db import get_db
from ..database.models import EvalResult
from ..audit.logger import get_audit_logs

router = APIRouter(prefix = "/audit", tags = ["Audit & Transparency"])

@router.get("/logs")
async def fetch_logs(limit: int = 50, db: Session = Depends(get_db)):
    """
    returns high-level query history for the main dashboard table
    """
    try:
        #fetches joined data from QueryLog and EvalResult
        logs = get_audit_logs(db, limit=limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit fetch failed: {str(e)}")

@router.get("/eval/{query_id}")
async def get_eval_detail(query_id: int, db: Session = Depends(get_db)):
    """
    Deep-dive endpoint for a single query's evaluation metrics.
    Used for the 'Why was this flagged?' drill-down view.
    """
    # Look up the evaluation record linked to the specific query ID
    eval_data = db.query(EvalResult).filter(EvalResult.query_log_id == query_id).first()
    
    if not eval_data:
        raise HTTPException(
            status_code=404, 
            detail="No evaluation results found for this query. It may have been blocked."
        )
    
    return {
        "query_log_id": eval_data.query_log_id,
        "metrics": {
            "faithfulness": eval_data.faithfulness_score,
            "relevance": eval_data.relevance_score,
            "confidence": eval_data.confidence_score,
            "hallucination": eval_data.hallucination_flag
        },
        "summary": eval_data.eval_summary,
        "reasoning": eval_data.reasoning_log,
        "evidence": eval_data.source_chunks
    }
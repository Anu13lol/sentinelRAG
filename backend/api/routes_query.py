from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database.db import get_db
from ..retrieval.retriever import retrieve_chunks
from ..llm.gemini_client import ask
from ..eval.scorer import run_eval
from ..audit.logger import log_query, log_eval

router = APIRouter(prefix="/query", tags=["Query"])

#request schema:
class QueryRequest(BaseModel):
    query: str

@router.post("/")
async def process_query(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Orchestration: Retrieve -> Generate -> Evaluate -> Log
    """
    query_text = request.query
    was_blocked = False
    
    try:
        #retrieval (MMR Search)
        #pulls the most relevant context chunks from ChromaDB
        chunks = retrieve_chunks(query_text, k=5)
        
        llm_response = ask(query_text, chunks)
        
        if llm_response["finish_reason"] in ["error", "SAFETY", "BLOCKED"]:
            answer_text = "[BLOCKED BY LOBSTER TRAP]"
            was_blocked = True
            eval_result = None
            
            # Log the blocked attempt for security auditing
            log_query(db, query_text, answer_text, was_blocked)
            
            return {
                "answer": answer_text,
                "was_blocked": True,
                "eval": None,
                "sources": [c['text'] for c in chunks]
            }
        #Normal flow - Evaluation
        answer_text = llm_response["answer"]
        eval_result = run_eval(query_text, answer_text, chunks)

        #Persistent Logging
        query_log = log_query(db, query_text, answer_text, was_blocked=False)
        log_eval(db, query_log.id, eval_result, chunks)

        return {
            "answer": answer_text,
            "eval": eval_result,
            "sources": [c['text'] for c in chunks],
            "was_blocked": False
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query Pipeline Error: {str(e)}")
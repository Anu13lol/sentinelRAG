import os
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.db import get_db
from ..database.models import Document
from ..ingestion.loader import load_and_chunk_pdf, load_csv_as_semantic_docs
from ..ingestion.embedder import embed_and_store

router = APIRouter(prefix = "/ingest", tags = ["Ingestion"])
    
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Ingests PDF/CSV files, generates embeddings and logs metadata
    """
    temp_path = os.path.join(tempfile.gettempdir(), file.filename)

    #save temp file to disk
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        #route based on file type
        file_ext = file.filename.split(".")[-1].lower()

        if file_ext == "pdf":
            chunks = load_and_chunk_pdf(temp_path)
        elif file_ext == "csv":
            chunks = load_csv_as_semantic_docs(temp_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use PDF or CSV")

        #Gemini embedding
        #pushing vectors to ChromaDB
        embed_and_store(chunks)

        #log to SQLite for document tracking
        new_doc = Document(
            filename=file.filename,
            file_type=file_ext,
            num_chunks=len(chunks),
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        return {
            "status": "success",
            "document_id": new_doc.id,
            "filename": file.filename,
            "chunks_stored": len(chunks)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail = f"Ingestion failed: {str(e)}")

    finally:
        #always delete temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

from datetime import datetime
import json

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from .db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key = True, autoincrement = True)
    filename = Column(String, nullable = False)
    file_type = Column(String) #csv or pdf
    num_chunks = Column(Integer)
    created_at = Column(DateTime, default = datetime.utcnow)

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key = True, autoincrement = True)
    query_text = Column(Text)
    answer_text = Column(Text)
    was_blocked = Column(Boolean, default = False)
    created_at = Column(DateTime, default = datetime.utcnow)

    # relating with EvalResult
    evaluation = relationship("EvalResult", back_populates="query_log", uselist=False)

class EvalResult(Base):
    __tablename__ = "eval_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_log_id = Column(Integer, ForeignKey("query_logs.id"), nullable=False)

    # Metrics for "XAI" and Trust
    faithfulness_score = Column(Float)
    relevance_score = Column(Float)
    hallucination_flag = Column(Boolean, default=False)
    confidence_score = Column(Float)
    eval_summary = Column(String(32), nullable=True)
    reasoning_log = Column(Text, nullable=True)

    # Store source_chunks as a JSON string for easy retrieval
    source_chunks = Column(Text)
    created_at = Column(DateTime, default = datetime.utcnow)

    query_log = relationship("QueryLog", back_populates="evaluation")

    def set_source_chunks(self, chunks_list):
        self.source_chunks = json.dumps(chunks_list)
    
    def get_source_chunks(self):
        return json.loads(self.source_chunks) if self.source_chunks else {}


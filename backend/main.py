from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database.db import init_db
from .database import models as _models  # noqa: F401 — register ORM metadata before create_all

from .api import routes_ingest
from .api import routes_query
from .api import routes_audit

from .llm.lobster_trap import get_lobster_trap_status

#api instance
app = FastAPI(
    title="SentinelRAG API",
    description="Enterprise AI Agent Auditor",
    version="1.0"
)

#init db on startup
#running the sync at the module level guarantees SQLite tables
init_db()

if get_lobster_trap_status():
    print("> Lobster Trap proxy is running")
else:
    print("!! WARNING: Lobster Trap proxy is not running on localhost:8080")
    
#CORS middleware config
#react frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

#include routers
app.include_router(routes_ingest.router)
app.include_router(routes_query.router)
app.include_router(routes_audit.router)

#root endpoint
@app.get("/")
async def root():
    """Health check endpoint to verify backend status."""
    return {"status": "SentinelRAG is running"}

@app.get("/status")
async def status():
    return{
        "backend": True,
        "lobster_trap": get_lobster_trap_status()
    }
    
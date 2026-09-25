import sys
from pathlib import Path

# Add backend directory to sys.path so modules and routers can be imported from anywhere
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import analytics, auth, cases, contradictions, entities, facts, relationships, sources, system

app = FastAPI(title="Profiling Facts API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "name": "Fact Ledger API",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health"
    }

app.include_router(system.router)
app.include_router(auth.router)
app.include_router(sources.router)
app.include_router(entities.router)
app.include_router(facts.router)
app.include_router(relationships.router)
app.include_router(contradictions.router)
app.include_router(analytics.router)
app.include_router(cases.router)


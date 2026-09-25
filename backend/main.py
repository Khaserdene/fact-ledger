"""Үнэний Бүртгэл — FastAPI аппликэйшн.

Схемийг Alembic удирдана: `alembic upgrade head` (start.bat автоматаар ажиллуулна).
"""
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

app.include_router(system.router)
app.include_router(auth.router)
app.include_router(sources.router)
app.include_router(entities.router)
app.include_router(facts.router)
app.include_router(relationships.router)
app.include_router(contradictions.router)
app.include_router(analytics.router)
app.include_router(cases.router)


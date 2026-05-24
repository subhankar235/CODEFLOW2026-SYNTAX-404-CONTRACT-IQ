from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.base import Base  # noqa: F401
    from app.models import (  # noqa: F401
        User,
        Contract,
        Clause,
        ScanJob,
        AnalysisResult,
        CounterOffer,
        PrecedentMatch,
        Report,
        Embedding,
    )

    yield


app = FastAPI(
    title="LegalTech AI Contract Scanner API",
    description="AI-powered legal contract analysis platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "api"}


@app.get("/")
async def root():
    return {"message": "LegalTech AI Contract Scanner API", "version": "1.0.0"}

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes.chat import router as chat_router
from app.api.routes.translate import router as translate_router
from app.api.routes.analyze import router as analyze_router
from app.api.routes.counter_offer import router as counter_offer_router
from app.api.routes.precedent import router as precedent_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="LegalTech AI Service",
    description="AI and NLP pipelines for contract analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(chat_router, prefix="/api/v1")
app.include_router(translate_router)
app.include_router(analyze_router, prefix="/api/v1")
app.include_router(counter_offer_router, prefix="/api/v1")
app.include_router(precedent_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai"}


@app.get("/")
async def root():
    return {"message": "LegalTech AI Service", "version": "1.0.0"}

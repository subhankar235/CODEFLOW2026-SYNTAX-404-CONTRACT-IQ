from fastapi import FastAPI

app = FastAPI(
    title="Contract-IQ AI Service",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai"}

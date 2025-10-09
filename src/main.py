from fastapi import FastAPI
from pydantic import BaseModel

from src.api.services import router as services_router


class HealthResponse(BaseModel):
    status: str


class RootResponse(BaseModel):
    name: str
    version: str
    status: str


app = FastAPI(
    title="LipService",
    description="AI-powered intelligent log sampling",
    version="0.1.0",
)

# Include routers
app.include_router(services_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="healthy")


@app.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    return RootResponse(
        name="LipService",
        version="0.1.0",
        status="in development",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

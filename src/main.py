from fastapi import FastAPI
from pydantic import BaseModel

from src.api.analysis import router as analysis_router
from src.api.patterns import router as patterns_router
from src.api.pipeline import router as pipeline_router
from src.api.policies import router as policies_router
from src.api.services import router as services_router
from src.api.intelligent_analysis import router as intelligent_analysis_router
from src.api.adaptive_filtering import router as adaptive_filtering_router


class HealthResponse(BaseModel):
    status: str


class RootResponse(BaseModel):
    name: str
    version: str
    status: str


app = FastAPI(
    title="LipService",
    description="AI-powered intelligent log sampling with semantic analysis and adaptive filtering",
    version="0.2.0",
)

# Include routers
app.include_router(services_router)
app.include_router(policies_router)
app.include_router(patterns_router)
app.include_router(analysis_router)
app.include_router(pipeline_router)
app.include_router(intelligent_analysis_router)
app.include_router(adaptive_filtering_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="healthy")


@app.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    return RootResponse(
        name="LipService",
        version="0.2.0",
        status="production ready",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

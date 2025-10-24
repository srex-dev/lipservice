"""
FastAPI integration example.

Shows how to integrate LipService with a FastAPI application.
"""

import structlog
from fastapi import FastAPI, HTTPException

from lipservice.integrations.fastapi import LipServiceMiddleware, configure_lipservice_fastapi

# Create FastAPI app
app = FastAPI(title="LipService FastAPI Example")

# Configure LipService
configure_lipservice_fastapi(
    service_name="fastapi-example",
    lipservice_url="http://localhost:8000",
)

# Add LipService middleware
app.add_middleware(LipServiceMiddleware)

# Get logger
logger = structlog.get_logger(__name__)


@app.get("/")
async def root():
    """Root endpoint."""
    logger.info("root_endpoint_accessed")
    return {"message": "Hello from LipService FastAPI example!"}


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID."""
    logger.info("get_user", user_id=user_id)

    if user_id < 1:
        logger.error("invalid_user_id", user_id=user_id)  # Always logged!
        raise HTTPException(status_code=400, detail="Invalid user ID")

    return {"user_id": user_id, "name": f"User {user_id}"}


@app.post("/orders")
async def create_order(order: dict):
    """Create order."""
    logger.info("create_order_start", order_data=order)

    # Simulate processing
    try:
        # Your business logic here
        logger.debug("processing_order", step="validation")
        logger.debug("processing_order", step="payment")
        logger.debug("processing_order", step="fulfillment")

        logger.info("order_created_successfully", order_id="12345")
        return {"order_id": "12345", "status": "created"}

    except Exception as e:
        logger.error("order_creation_failed", error=str(e))  # Always logged!
        raise HTTPException(status_code=500, detail="Order creation failed")


@app.get("/health")
async def health():
    """Health check endpoint."""
    # Health checks are typically noisy - LipService will sample these
    logger.debug("health_check")
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    print("🎙️ Starting LipService FastAPI Example")
    print("=" * 60)
    print("\nAvailable endpoints:")
    print("  GET  / - Root endpoint")
    print("  GET  /users/{user_id} - Get user")
    print("  POST /orders - Create order")
    print("  GET  /health - Health check")
    print("\nLogs are being intelligently sampled!")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=3000)


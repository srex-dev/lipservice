from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.storage.database import get_db
from src.storage.models import Service

router = APIRouter(prefix="/api/v1/services", tags=["services"])


class ServiceCreate(BaseModel):
    team_id: int
    name: str


class ServiceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    team_id: int
    name: str
    is_active: bool


@router.post("/", response_model=ServiceResponse, status_code=201)
async def create_service(service: ServiceCreate, db: Session = Depends(get_db)) -> ServiceResponse:
    """Create a new service to monitor."""
    db_service = Service(team_id=service.team_id, name=service.name)
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return ServiceResponse.model_validate(db_service)


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: int, db: Session = Depends(get_db)) -> ServiceResponse:
    """Get service by ID."""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return ServiceResponse.model_validate(service)


@router.get("/", response_model=list[ServiceResponse])
async def list_services(team_id: int | None = None, db: Session = Depends(get_db)) -> list[ServiceResponse]:
    """List all services, optionally filtered by team_id."""
    query = db.query(Service)
    if team_id:
        query = query.filter(Service.team_id == team_id)
    services = query.all()
    return [ServiceResponse.model_validate(s) for s in services]

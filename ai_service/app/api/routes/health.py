"""
Health check and system status routes
"""
from fastapi import APIRouter
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns the current status and version of the service.
    """
    return HealthResponse(
        status="healthy",
        service="AI Microservice - Generation Mode",
        version="1.0.0"
    )


@router.get("/health", response_model=HealthResponse)
async def detailed_health():
    """
    Detailed health check endpoint.
    Can be extended to include database connectivity, LLM availability, etc.
    """
    # TODO: Add checks for:
    # - Database connectivity
    # - LLM API availability
    # - Memory/CPU usage
    
    return HealthResponse(
        status="healthy",
        service="AI Microservice - Generation Mode",
        version="1.0.0"
    )

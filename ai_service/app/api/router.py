"""
Main API Router
Aggregates all route modules
"""
from fastapi import APIRouter
from app.api.routes import health, sessions, chat

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router)
api_router.include_router(sessions.router)
api_router.include_router(chat.router)

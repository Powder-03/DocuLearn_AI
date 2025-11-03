"""
Main FastAPI Application Entry Point
Clean, modular structure with async REST API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.models import Base
from app.db.session import engine
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown tasks.
    Replaces deprecated @app.on_event decorators.
    """
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    print("✅ AI Microservice started successfully")
    print(f"📊 Environment: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    
    yield
    
    # Shutdown: Cleanup tasks
    print("🛑 AI Microservice shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="DocuLearn AI - Generation Mode",
    description="Async REST API for AI-powered personalized learning with LangGraph",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes with prefix
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with service information and available endpoints."""
    return {
        "service": "DocuLearn AI - Generation Mode",
        "version": "2.0.0",
        "status": "operational",
        "description": "AI-powered personalized learning microservice",
        "docs": "/docs",
        "api_prefix": "/api/v1",
        "endpoints": {
            "health": {
                "root": "GET /api/v1/",
                "health": "GET /api/v1/health"
            },
            "sessions": {
                "create": "POST /api/v1/sessions/create",
                "details": "GET /api/v1/sessions/{session_id}",
                "lesson_plan": "GET /api/v1/sessions/{session_id}/lesson-plan"
            },
            "chat": {
                "invoke": "POST /api/v1/chat/invoke",
                "stream": "POST /api/v1/chat/stream",
                "state": "GET /api/v1/chat/state/{session_id}"
            }
        },
        "features": [
            "Async REST API (FastAPI)",
            "Server-Sent Events streaming",
            "PostgreSQL persistence",
            "LangGraph orchestration",
            "Dual LLM (Gemini + GPT-4)"
        ],
        "authentication": "Handled by separate Cognito microservice"
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

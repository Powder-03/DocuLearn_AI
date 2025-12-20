"""
Main FastAPI Application Entry Point
Clean, modular structure with async REST API
"""
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from contextlib import asynccontextmanager

# --- Configure Logging ---
# This setup ensures logs are formatted and sent to stdout/stderr,
# which is the standard for containerized applications and Google Cloud Run.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)
# --- End Logging Configuration ---

from app.core.config import settings
from app.db.models import Base
from app.db.session import engine
from app.api.router import api_router
from app.services.mongodb import mongodb_service

# Debug log to verify app loading
logger.info("🔍 Loading DocuLearn AI Service module...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events."""
    try:
        # Startup
        logger.info("🚀 Starting DocuLearn AI Service...")
        logger.info("📊 Cloud Infrastructure:")
        logger.info("   - PostgreSQL: Google Cloud SQL")
        logger.info("   - MongoDB: Atlas Cloud")
        logger.info(f"   - LLM: Google Gemini ({settings.PLANNING_LLM_MODEL})")
        
        # MongoDB connection is now handled lazily by the service itself
        # on the first request that needs it. This speeds up startup.
        
        logger.info("✅ DocuLearn AI Service ready for production!")
        
        yield
        
        # Shutdown
        logger.info("🛑 Shutting down DocuLearn AI Service...")
        await mongodb_service.close()
        logger.info("✅ Connections closed")
        
    except Exception as e:
        logger.critical(f"❌ FATAL: Application startup failed: {e}", exc_info=True)
        # Re-raise the exception to ensure the container exits and Cloud Run reports a failure.
        raise


# Initialize FastAPI app
app = FastAPI(
    title="DocuLearn AI - Production",
    description="AI-powered learning with Google Gemini, Neon PostgreSQL, and MongoDB Atlas",
    version="2.1.0",
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
        "service": "DocuLearn AI - Production Ready",
        "version": "2.1.0",
        "status": "operational",
        "description": "AI-powered personalized learning microservice",
        "infrastructure": {
            "llm_provider": "Google Gemini",
            "llm_model": settings.PLANNING_LLM_MODEL,
            "database": "Neon PostgreSQL (Cloud)",
            "chat_storage": "MongoDB Atlas (Cloud)",
            "deployment": "AWS Lambda Ready"
        },
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
            "100% Cloud Infrastructure",
            "Neon PostgreSQL (Serverless)",
            "MongoDB Atlas (Managed)",
            "Google Gemini LLM",
            "AWS Lambda Compatible",
            "Zero local dependencies",
            "Production ready"
        ],
        "authentication": "Handled by separate Cognito microservice"
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )

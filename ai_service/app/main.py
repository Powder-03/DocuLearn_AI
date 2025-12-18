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
from app.services.mongodb import mongodb_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events."""
    # Startup
    print("🚀 Starting DocuLearn AI Service...")
    print("📊 Cloud Infrastructure:")
    print("   - PostgreSQL: Neon Cloud")
    print("   - MongoDB: Atlas Cloud")
    print(f"   - LLM: Groq ({settings.PLANNING_LLM_MODEL})")
    
    # Create database tables in Neon
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Neon PostgreSQL tables created/verified")
    except Exception as e:
        print(f"⚠️  PostgreSQL setup warning: {e}")
    
    # Connect to MongoDB Atlas
    try:
        await mongodb_service.connect()
        print("✅ MongoDB Atlas connected")
    except Exception as e:
        print(f"❌ MongoDB Atlas connection failed: {e}")
        raise
    
    print("✅ DocuLearn AI Service ready for production!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down DocuLearn AI Service...")
    await mongodb_service.close()
    print("✅ Connections closed")


# Initialize FastAPI app
app = FastAPI(
    title="DocuLearn AI - Production",
    description="AI-powered learning with Groq Llama 3.1 70B, Neon PostgreSQL, and MongoDB Atlas",
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
            "llm_provider": "Groq",
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
            "Groq LLM (Ultra-fast)",
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
        port=8001,
        reload=True,
        log_level="info"
    )

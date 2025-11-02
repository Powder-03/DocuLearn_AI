"""
Main FastAPI Application Entry Point
Clean, modular structure with separated concerns
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.models import Base
from app.db.session import engine
from app.api.router import api_router
from app.api.routes.langserve import setup_langserve_routes


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
    
    yield
    
    # Shutdown: Cleanup tasks
    print("🛑 AI Microservice shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="DocuLearn AI - Generation Mode",
    description="LangGraph-powered personalized learning microservice with PostgreSQL persistence",
    version="1.0.0",
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

# Include API routes
app.include_router(api_router)

# Setup LangServe routes (separate from REST API)
setup_langserve_routes(app)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

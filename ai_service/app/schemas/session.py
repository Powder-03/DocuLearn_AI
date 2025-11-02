"""
Session-related Pydantic models
Request and response schemas for learning sessions
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class CreatePlanRequest(BaseModel):
    """Request model for creating a new learning plan."""
    user_id: str = Field(
        ..., 
        description="UUID of the authenticated user",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    topic: str = Field(
        ..., 
        description="Learning topic",
        min_length=3,
        max_length=200,
        examples=["Introduction to Python Programming"]
    )
    total_days: int = Field(
        ..., 
        description="Number of days for the learning plan",
        ge=1,
        le=30,
        examples=[7]
    )
    time_per_day: str = Field(
        ..., 
        description="Time commitment per day",
        examples=["30 minutes", "1 hour", "45 minutes"]
    )

    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Ensure topic is not empty or just whitespace."""
        if not v.strip():
            raise ValueError("Topic cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic": "Machine Learning Fundamentals",
                "total_days": 7,
                "time_per_day": "45 minutes"
            }
        }


class CreatePlanResponse(BaseModel):
    """Response model for plan creation."""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="Success message")
    topic: str = Field(..., description="The learning topic")
    total_days: int = Field(..., description="Total days in the plan")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
                "message": "Learning plan created successfully",
                "topic": "Machine Learning Fundamentals",
                "total_days": 7
            }
        }


class SessionResponse(BaseModel):
    """Response model for session retrieval."""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    topic: str = Field(..., description="Learning topic")
    current_day: int = Field(..., description="Current day in the plan")
    total_days: int = Field(..., description="Total days in the plan")
    has_lesson_plan: bool = Field(..., description="Whether lesson plan exists")
    message_count: int = Field(..., description="Number of chat messages")
    created_at: Optional[str] = Field(None, description="Session creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic": "Machine Learning Fundamentals",
                "current_day": 3,
                "total_days": 7,
                "has_lesson_plan": True,
                "message_count": 15,
                "created_at": "2025-11-03T10:30:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "AI Microservice - Generation Mode",
                "version": "1.0.0"
            }
        }

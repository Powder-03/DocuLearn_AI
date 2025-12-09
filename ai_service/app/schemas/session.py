"""
Session-related Pydantic models
Request and response schemas for learning sessions
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


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


class ChatRequest(BaseModel):
    """Request model for synchronous chat."""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User's message", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
                "message": "Can you explain what a neural network is?"
            }
        }


class ChatResponse(BaseModel):
    """Response model for synchronous chat."""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="AI tutor's response")
    current_day: int = Field(..., description="Current day in the plan")
    lesson_plan_exists: bool = Field(..., description="Whether lesson plan exists")
    metadata: dict = Field(..., description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
                "message": "Great question! Let me guide you through neural networks...",
                "current_day": 3,
                "lesson_plan_exists": True,
                "metadata": {
                    "day_title": "Introduction to Neural Networks",
                    "total_days": 7,
                    "message_count": 16
                }
            }
        }


class StreamChatRequest(BaseModel):
    """Request model for streaming chat."""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User's message", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
                "message": "Tell me about backpropagation"
            }
        }


class GraphStateResponse(BaseModel):
    """Response model for graph state inspection."""
    session_id: str = Field(..., description="Session identifier")
    current_day: int = Field(..., description="Current day")
    lesson_plan_exists: bool = Field(..., description="Whether plan exists")
    total_messages: int = Field(..., description="Number of messages")
    next_node: Optional[str] = Field(None, description="Next node to execute")
    metadata: dict = Field(..., description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
                "current_day": 3,
                "lesson_plan_exists": True,
                "total_messages": 15,
                "next_node": "tutor",
                "metadata": {
                    "topic": "Machine Learning Fundamentals",
                    "total_days": 7,
                    "time_per_day": "45 minutes"
                }
            }
        }


class CreateSessionRequest(BaseModel):
    """Request model for creating a new learning session"""
    user_id: str = Field(..., min_length=1, description="User identifier from authentication service")
    topic: str = Field(..., min_length=1, max_length=500, description="Learning topic")
    total_days: int = Field(7, ge=1, le=365, description="Total days for learning plan")
    time_per_day: str = Field("30 minutes", description="Time commitment per day")
    
    @field_validator('topic')
    @classmethod
    def topic_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Topic cannot be empty')
        return v.strip()


class SessionSummary(BaseModel):
    """Summary of a session for list views"""
    session_id: str
    topic: str
    current_day: int
    total_days: int
    time_per_day: str
    is_completed: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class SessionListResponse(BaseModel):
    """Response model for listing sessions"""
    total: int
    skip: int
    limit: int
    sessions: List[SessionSummary]


class SessionStatsResponse(BaseModel):
    """Response model for user learning statistics"""
    total_sessions: int
    completed_sessions: int
    in_progress_sessions: int
    total_days_planned: int
    total_days_completed: int
    completion_rate: float

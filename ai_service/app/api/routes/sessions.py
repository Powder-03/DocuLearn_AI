"""
Learning session management routes
Handles session creation, retrieval, and management
"""
import uuid
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from app.schemas import (
    CreatePlanRequest,
    CreatePlanResponse,
    SessionResponse
)
from app.services.memory import create_session, get_session_state
from app.graphs.generation_graph import generation_app

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/create", response_model=CreatePlanResponse, status_code=status.HTTP_201_CREATED)
async def create_learning_plan(request: CreatePlanRequest) -> CreatePlanResponse:
    """
    Create a new learning session and generate an initial lesson plan.
    
    This endpoint:
    1. Generates a new session_id
    2. Creates a database record
    3. Invokes the generation_app to trigger plan_generator_node
    4. Returns the session_id for future interactions
    
    **Args:**
    - **user_id**: UUID of the authenticated user
    - **topic**: The subject/topic to learn
    - **total_days**: Number of days for the learning plan (1-30)
    - **time_per_day**: Daily time commitment (e.g., "30 minutes")
    
    **Returns:**
    - **session_id**: Unique identifier for this learning session
    - **message**: Success confirmation message
    - **topic**: The learning topic
    - **total_days**: Plan duration
    """
    try:
        # Generate new session ID
        session_id = str(uuid.uuid4())
        
        # Create session in database
        initial_state = create_session(
            session_id=session_id,
            user_id=request.user_id,
            topic=request.topic,
            total_days=request.total_days,
            time_per_day=request.time_per_day
        )
        
        # Invoke the graph to trigger planning
        # This will execute the plan_generator_node
        result = generation_app.invoke(initial_state)
        
        return CreatePlanResponse(
            session_id=session_id,
            message="Learning plan created successfully",
            topic=request.topic,
            total_days=request.total_days
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create plan: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_details(session_id: str) -> SessionResponse:
    """
    Retrieve the current state of a learning session.
    
    Useful for:
    - Debugging session state
    - Monitoring learning progress
    - Dashboard displays
    - Analytics
    
    **Args:**
    - **session_id**: UUID of the learning session
    
    **Returns:**
    - Complete session metadata and progress information
    
    **Raises:**
    - **404**: Session not found
    - **500**: Database error
    """
    try:
        state = get_session_state(session_id)
        
        return SessionResponse(
            session_id=state["session_id"],
            user_id=state["user_id"],
            topic=state["topic"],
            current_day=state["current_day"],
            total_days=state["total_days"],
            has_lesson_plan=state["lesson_plan"] is not None,
            message_count=len(state["chat_history"]),
            created_at=None  # TODO: Add timestamp from DB
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.get("/{session_id}/lesson-plan")
async def get_lesson_plan(session_id: str) -> Dict[str, Any]:
    """
    Retrieve the lesson plan for a specific session.
    
    **Args:**
    - **session_id**: UUID of the learning session
    
    **Returns:**
    - The complete lesson plan JSON
    """
    try:
        state = get_session_state(session_id)
        lesson_plan = state.get("lesson_plan")
        
        if not lesson_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson plan not yet generated for this session"
            )
        
        return {
            "session_id": session_id,
            "lesson_plan": lesson_plan,
            "current_day": state["current_day"]
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve lesson plan: {str(e)}"
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    """
    Delete a learning session.
    
    **Note:** This is a soft delete - the session is marked as inactive
    but data is retained for analytics.
    
    **Args:**
    - **session_id**: UUID of the learning session to delete
    """
    # TODO: Implement soft delete logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Session deletion not yet implemented"
    )

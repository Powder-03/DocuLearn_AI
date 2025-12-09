"""
Learning session management routes - Thin controllers
Delegates all business logic to session_service
"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional

from app.schemas.session import (
    CreateSessionRequest,
    SessionResponse,
    SessionListResponse,
    SessionStatsResponse,
    CreatePlanRequest,
    CreatePlanResponse
)
from app.services.session_service import session_service

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest):
    """
    Create a new learning session
    
    Creates a structured learning plan for the specified topic.
    """
    try:
        result = session_service.create_session(
            user_id=request.user_id,
            topic=request.topic,
            total_days=request.total_days,
            time_per_day=request.time_per_day
        )
        return SessionResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")


@router.post("/create", response_model=CreatePlanResponse, status_code=status.HTTP_201_CREATED)
async def create_learning_plan(request: CreatePlanRequest) -> CreatePlanResponse:
    """
    Create a new learning session (legacy endpoint for backward compatibility)
    
    This endpoint maintains compatibility with existing API contracts.
    """
    try:
        result = session_service.create_session(
            user_id=request.user_id,
            topic=request.topic,
            total_days=request.total_days,
            time_per_day=request.time_per_day
        )
        return CreatePlanResponse(
            session_id=result["session_id"],
            message=result["message"],
            topic=result["topic"],
            total_days=result["total_days"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create plan: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authorization")
):
    """
    Get details of a specific session
    """
    try:
        session = session_service.get_session(session_id, user_id)
        
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
        return SessionResponse(**session)
        
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error retrieving session: {str(e)}")


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    user_id: str = Query(..., description="User ID from authentication service"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    include_completed: bool = Query(True, description="Include completed sessions")
):
    """
    List all sessions for a user with pagination
    """
    try:
        result = session_service.list_user_sessions(
            user_id=user_id,
            skip=skip,
            limit=limit,
            include_completed=include_completed
        )
        return SessionListResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error listing sessions: {str(e)}")


@router.patch("/{session_id}/progress")
async def update_progress(
    session_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authorization")
):
    """
    Advance session to next day
    """
    try:
        result = session_service.update_session_progress(
            session_id=session_id,
            user_id=user_id,
            increment_day=True
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating progress: {str(e)}")


@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
async def delete_session(
    session_id: str,
    user_id: Optional[str] = Query(None, description="User ID for authorization")
):
    """
    Delete a session and all associated data
    """
    try:
        result = session_service.delete_session(session_id, user_id)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting session: {str(e)}")


@router.get("/stats/{user_id}", response_model=SessionStatsResponse)
async def get_user_statistics(user_id: str):
    """
    Get learning statistics for a user
    """
    try:
        stats = session_service.get_session_statistics(user_id)
        return SessionStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching statistics: {str(e)}")


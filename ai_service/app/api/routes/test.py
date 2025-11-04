"""
Test endpoints for development - bypasses authentication
⚠️ FOR DEVELOPMENT ONLY - REMOVE IN PRODUCTION
"""
from fastapi import APIRouter, HTTPException

from app.services.session_service import session_service
from app.services.chat_service import chat_service
from app.services.mongodb import mongodb_service

router = APIRouter(prefix="/test", tags=["Testing (Dev Only)"])

TEST_USER_ID = "test-user-123"


@router.post("/session")
async def create_test_session(
    topic: str,
    total_days: int = 7,
    time_per_day: str = "30 minutes"
):
    """
    Create a test session without authentication
    
    **⚠️ FOR DEVELOPMENT ONLY - REMOVE IN PRODUCTION**
    
    Example:
    ```
    POST /api/test/session?topic=Python%20Programming&total_days=7&time_per_day=30%20minutes
    ```
    """
    try:
        result = session_service.create_session(
            user_id=TEST_USER_ID,
            topic=topic,
            total_days=total_days,
            time_per_day=time_per_day
        )
        return {
            **result,
            "info": "⚠️ Using test user ID - authentication bypassed"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions")
async def list_test_sessions():
    """
    List all test sessions
    
    **⚠️ FOR DEVELOPMENT ONLY**
    """
    try:
        result = session_service.list_user_sessions(user_id=TEST_USER_ID)
        return {
            "test_user_id": TEST_USER_ID,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@router.get("/session/{session_id}")
async def get_test_session(session_id: str):
    """
    Get a test session by ID
    
    **⚠️ FOR DEVELOPMENT ONLY**
    """
    try:
        session = session_service.get_session(session_id, TEST_USER_ID)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_test_session(session_id: str):
    """
    Delete a test session and its chat history
    
    **⚠️ FOR DEVELOPMENT ONLY**
    """
    try:
        # Delete session
        result = session_service.delete_session(session_id, TEST_USER_ID)
        
        # Delete chat history from MongoDB
        await mongodb_service.delete_session_chats(session_id)
        
        return {
            **result,
            "chat_history_deleted": True
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")


@router.get("/stats")
async def get_test_stats():
    """
    Get statistics for the test user
    
    **⚠️ FOR DEVELOPMENT ONLY**
    """
    try:
        stats = session_service.get_session_statistics(TEST_USER_ID)
        return {
            "test_user_id": TEST_USER_ID,
            **stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/chat")
async def test_chat(session_id: str, message: str):
    """
    Send a test chat message without authentication
    
    **⚠️ FOR DEVELOPMENT ONLY**
    
    Example:
    ```
    POST /api/test/chat?session_id=xxx&message=What should I learn first?
    ```
    """
    try:
        # Verify session belongs to test user
        session = session_service.get_session(session_id, TEST_USER_ID)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        result = await chat_service.process_chat_message(
            session_id=session_id,
            message=message
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.get("/chat/history/{session_id}")
async def get_test_chat_history(session_id: str, limit: int = 20):
    """
    Get chat history for a test session
    
    **⚠️ FOR DEVELOPMENT ONLY**
    """
    try:
        # Verify session belongs to test user
        session = session_service.get_session(session_id, TEST_USER_ID)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        history = await chat_service.get_chat_history(
            session_id=session_id,
            limit=limit,
            skip=0
        )
        return history
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/info")
async def test_info():
    """
    Get information about test endpoints and the test user
    
    **⚠️ FOR DEVELOPMENT ONLY**
    """
    return {
        "message": "Test endpoints active - FOR DEVELOPMENT ONLY",
        "test_user_id": TEST_USER_ID,
        "warning": "⚠️ These endpoints bypass authentication and should be REMOVED in production",
        "available_endpoints": {
            "info": "GET /api/test/info - This endpoint",
            "create_session": "POST /api/test/session?topic=...&total_days=7&time_per_day=30 minutes",
            "list_sessions": "GET /api/test/sessions",
            "get_session": "GET /api/test/session/{session_id}",
            "delete_session": "DELETE /api/test/session/{session_id}",
            "get_stats": "GET /api/test/stats",
            "chat": "POST /api/test/chat?session_id=xxx&message=your message",
            "chat_history": "GET /api/test/chat/history/{session_id}"
        },
        "usage_example": {
            "step_1": "Create a session: POST /api/test/session?topic=Python&total_days=7",
            "step_2": "Copy the session_id from response",
            "step_3": "Chat: POST /api/test/chat?session_id={session_id}&message=Hello",
            "step_4": "View history: GET /api/test/chat/history/{session_id}",
            "step_5": "View session: GET /api/test/session/{session_id}",
            "step_6": "Delete when done: DELETE /api/test/session/{session_id}"
        },
        "swagger_ui": "Visit http://localhost:8001/docs for interactive testing"
    }

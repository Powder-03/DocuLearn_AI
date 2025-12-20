"""
Chat endpoints for AI tutor interactions
Thin API layer - delegates all business logic to chat_service
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sse_starlette.sse import EventSourceResponse
import json
from sqlalchemy.orm import Session

from app.schemas.session import (
    ChatRequest, 
    ChatResponse, 
    StreamChatRequest,
    GraphStateResponse
)
from app.services.chat_service import chat_service
from app.api.deps import get_db

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/invoke", response_model=ChatResponse)
async def chat_invoke(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message and get AI tutor's response (non-streaming).
    
    ✅ Clean API layer - delegates to service
    
    **Example Request:**
    ```json
    {
        "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
        "message": "Can you explain Python variables?"
    }
    ```
    """
    try:
        result = await chat_service.process_chat_message(
            db=db,
            session_id=request.session_id,
            message=request.message
        )
        
        return ChatResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/stream")
async def chat_stream(request: StreamChatRequest, db: Session = Depends(get_db)):
    """
    Send a message and stream AI response in real-time using Server-Sent Events.
    
    ✅ Clean API layer - delegates to service
    
    **Benefits:**
    - Better user experience (typewriter effect)
    - Lower perceived latency
    - Real-time feedback
    """
    async def event_generator():
        async for chunk in chat_service.stream_chat_message(
            db=db,
            session_id=request.session_id,
            message=request.message
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return EventSourceResponse(event_generator())


@router.get("/state/{session_id}", response_model=GraphStateResponse)
async def get_graph_state(session_id: str, db: Session = Depends(get_db)):
    """
    Get the current state of the LangGraph for a session.
    
    ✅ Clean API layer - delegates to service
    
    **Use Cases:**
    - Debugging and monitoring
    - Progress tracking
    - Analytics dashboard
    """
    try:
        state_data = await chat_service.get_graph_state(session_id, db=db)
        return GraphStateResponse(**state_data)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"State retrieval error: {str(e)}")


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=100, description="Max messages to return"),
    skip: int = Query(0, ge=0, description="Messages to skip for pagination")
):
    """
    Get chat history for a session from MongoDB.
    
    ✅ Clean API layer - delegates to service
    """
    try:
        history = await chat_service.get_chat_history(
            session_id=session_id,
            limit=limit,
            skip=skip
        )
        
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History retrieval error: {str(e)}")


@router.delete("/history/{session_id}", status_code=204)
async def delete_chat_history(session_id: str):
    """
    Delete all chat history for a session from MongoDB.
    
    ✅ Clean API layer - delegates to service
    
    **Warning:** This action cannot be undone!
    """
    try:
        deleted_count = await chat_service.delete_chat_history(session_id)
        
        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="No chat history found for this session"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

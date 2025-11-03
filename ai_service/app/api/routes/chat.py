"""
Chat endpoints for AI tutor interactions
Full async REST API implementation with MongoDB chat storage
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import AsyncIterator
from sse_starlette.sse import EventSourceResponse
import json

from app.schemas.session import (
    ChatRequest, 
    ChatResponse, 
    StreamChatRequest,
    GraphStateResponse
)
from app.graphs.generation_graph import generation_app
from app.services.memory import get_session_state
from app.services.mongodb import mongodb_service
from app.api.deps import get_db
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/invoke", response_model=ChatResponse)
async def chat_invoke(
    request: ChatRequest,
    db = Depends(get_db)
):
    """
    Send a message and get AI tutor's response (non-streaming).
    
    This endpoint:
    1. Validates the session exists
    2. Adds user message to chat history
    3. Invokes the LangGraph asynchronously
    4. Returns the AI response
    
    **Flow:**
    - User sends message
    - Graph processes with current lesson context
    - AI tutor responds using Socratic method
    
    **Example Request:**
    ```json
    {
        "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
        "message": "Can you explain Python variables?"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
        "message": "Great question! Variables are containers...",
        "current_day": 1,
        "lesson_plan_exists": true,
        "metadata": {
            "day_title": "Introduction to Python",
            "total_days": 7,
            "message_count": 5
        }
    }
    ```
    """
    try:
        # Get session state from PostgreSQL
        session_data = get_session_state(request.session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Save user message to MongoDB
        await mongodb_service.save_message(
            session_id=request.session_id,
            user_id=session_data["user_id"],
            role="user",
            content=request.message,
            metadata={"current_day": session_data.get("current_day", 1)}
        )
        
        # Get recent chat history from MongoDB
        recent_messages = await mongodb_service.get_recent_messages(
            session_id=request.session_id,
            count=20  # Get last 20 messages for context
        )
        
        # Convert MongoDB messages to LangChain format
        chat_history = []
        for msg in recent_messages:
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            else:
                chat_history.append(AIMessage(content=msg["content"]))
        
        # Prepare graph state
        graph_state = {
            "session_id": request.session_id,
            "user_id": session_data["user_id"],
            "topic": session_data["topic"],
            "lesson_plan": session_data.get("lesson_plan"),
            "current_day": session_data.get("current_day", 1),
            "chat_history": chat_history,
            "total_days": session_data.get("total_days", 7),
            "time_per_day": session_data.get("time_per_day", "30 minutes")
        }
        
        # Invoke graph asynchronously
        config = {"configurable": {"thread_id": request.session_id}}
        result = await generation_app.ainvoke(graph_state, config=config)
        
        # Extract AI response
        ai_message = result["chat_history"][-1]
        
        # Save AI response to MongoDB
        await mongodb_service.save_message(
            session_id=request.session_id,
            user_id=session_data["user_id"],
            role="assistant",
            content=ai_message.content,
            metadata={
                "current_day": result.get("current_day", 1),
                "lesson_plan_exists": result.get("lesson_plan") is not None
            }
        )
        
        # Get current day info
        day_title = _get_current_day_title(result)
        
        # Get total message count
        total_messages = await mongodb_service.get_message_count(request.session_id)
        
        return ChatResponse(
            session_id=request.session_id,
            message=ai_message.content,
            current_day=result.get("current_day", 1),
            lesson_plan_exists=result.get("lesson_plan") is not None,
            metadata={
                "day_title": day_title,
                "total_days": result.get("lesson_plan", {}).get("total_days", 0) if result.get("lesson_plan") else 0,
                "message_count": total_messages
            }
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/stream")
async def chat_stream(request: StreamChatRequest):
    """
    Send a message and stream AI response in real-time using Server-Sent Events.
    
    **Benefits:**
    - Better user experience (typewriter effect)
    - Lower perceived latency
    - Real-time feedback
    
    **Client Example (JavaScript):**
    ```javascript
    const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            message: userMessage
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value);
        const lines = text.split('\\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                console.log(data);
            }
        }
    }
    ```
    
    **Client Example (Python):**
    ```python
    import requests
    import json
    
    response = requests.post(
        'http://localhost:8001/api/v1/chat/stream',
        json={'session_id': session_id, 'message': message},
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode('utf-8').replace('data: ', ''))
            print(data)
    ```
    """
    async def event_generator() -> AsyncIterator[str]:
        try:
            # Get session state from PostgreSQL
            session_data = get_session_state(request.session_id)
            
            if not session_data:
                yield f"data: {json.dumps({'event': 'error', 'data': 'Session not found'})}\n\n"
                return
            
            # Save user message to MongoDB
            await mongodb_service.save_message(
                session_id=request.session_id,
                user_id=session_data["user_id"],
                role="user",
                content=request.message,
                metadata={"current_day": session_data.get("current_day", 1)}
            )
            
            # Get recent chat history from MongoDB
            recent_messages = await mongodb_service.get_recent_messages(
                session_id=request.session_id,
                count=20
            )
            
            # Convert to LangChain format
            chat_history = []
            for msg in recent_messages:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                else:
                    chat_history.append(AIMessage(content=msg["content"]))
            
            # Prepare graph state
            graph_state = {
                "session_id": request.session_id,
                "user_id": session_data["user_id"],
                "topic": session_data["topic"],
                "lesson_plan": session_data.get("lesson_plan"),
                "current_day": session_data.get("current_day", 1),
                "chat_history": chat_history,
                "total_days": session_data.get("total_days", 7),
                "time_per_day": session_data.get("time_per_day", "30 minutes")
            }
            
            config = {"configurable": {"thread_id": request.session_id}}
            
            # Send start event
            yield f"data: {json.dumps({'event': 'start', 'data': 'Generating response...'})}\n\n"
            
            # Stream chunks from the graph
            full_response = ""
            async for chunk in generation_app.astream(graph_state, config=config):
                if "chat_history" in chunk and chunk["chat_history"]:
                    message = chunk["chat_history"][-1]
                    
                    if hasattr(message, 'content') and message.content:
                        content_chunk = message.content[len(full_response):]
                        full_response = message.content
                        
                        if content_chunk:
                            yield f"data: {json.dumps({
                                'event': 'token',
                                'data': content_chunk,
                                'metadata': {
                                    'current_day': chunk.get('current_day', 1),
                                    'progress': len(full_response)
                                }
                            })}\n\n"
            
            # Save AI response to MongoDB
            if full_response:
                await mongodb_service.save_message(
                    session_id=request.session_id,
                    user_id=session_data["user_id"],
                    role="assistant",
                    content=full_response,
                    metadata={
                        "current_day": session_data.get("current_day", 1),
                        "lesson_plan_exists": session_data.get("lesson_plan") is not None
                    }
                )
            
            # Get total message count
            total_messages = await mongodb_service.get_message_count(request.session_id)
            
            # Send completion event
            yield f"data: {json.dumps({
                'event': 'done',
                'data': 'Stream complete',
                'metadata': {
                    'total_chars': len(full_response),
                    'current_day': session_data.get('current_day', 1),
                    'total_messages': total_messages
                }
            })}\n\n"
            
        except ValueError as e:
            yield f"data: {json.dumps({'event': 'error', 'data': str(e)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'data': f'Streaming error: {str(e)}'})}\n\n"
    
    return EventSourceResponse(event_generator())


@router.get("/state/{session_id}", response_model=GraphStateResponse)
async def get_graph_state(session_id: str):
    """
    Get the current state of the LangGraph for a session.
    
    **Use Cases:**
    - Debugging and monitoring
    - Progress tracking
    - Analytics dashboard
    - Resume interrupted sessions
    - Check if plan generation is complete
    
    **Response includes:**
    - Current day in lesson plan
    - Whether lesson plan exists
    - Total message count (from MongoDB)
    - Next node to execute (for debugging)
    - Full metadata (topic, plan, etc.)
    """
    try:
        # Try to get state from graph checkpointer first
        config = {"configurable": {"thread_id": session_id}}
        state_snapshot = generation_app.get_state(config)
        
        # Get message count from MongoDB
        total_messages = await mongodb_service.get_message_count(session_id)
        
        if state_snapshot and state_snapshot.values:
            state_values = state_snapshot.values
            
            return GraphStateResponse(
                session_id=session_id,
                current_day=state_values.get("current_day", 1),
                lesson_plan_exists=state_values.get("lesson_plan") is not None,
                total_messages=total_messages,
                next_node=state_snapshot.next[0] if state_snapshot.next else None,
                metadata={
                    "topic": state_values.get("topic"),
                    "total_days": state_values.get("total_days", 0),
                    "time_per_day": state_values.get("time_per_day"),
                    "lesson_plan_summary": _get_lesson_plan_summary(state_values.get("lesson_plan")),
                    "source": "graph_checkpointer"
                }
            )
        
        # Fallback to database
        session_data = get_session_state(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session state not found")
        
        return GraphStateResponse(
            session_id=session_id,
            current_day=session_data.get("current_day", 1),
            lesson_plan_exists=session_data.get("lesson_plan") is not None,
            total_messages=total_messages,
            next_node=None,
            metadata={
                "topic": session_data.get("topic"),
                "total_days": session_data.get("total_days", 0),
                "time_per_day": session_data.get("time_per_day"),
                "source": "database"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"State retrieval error: {str(e)}")


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    skip: int = 0
):
    """
    Get chat history for a session from MongoDB.
    
    **Args:**
    - **session_id**: Session identifier
    - **limit**: Maximum number of messages (default: 50, max: 100)
    - **skip**: Number of messages to skip for pagination (default: 0)
    
    **Returns:**
    - List of chat messages with metadata
    
    **Example:**
    ```bash
    curl "http://localhost:8001/api/v1/chat/history/{session_id}?limit=20&skip=0"
    ```
    """
    try:
        # Validate limits
        if limit > 100:
            limit = 100
        if skip < 0:
            skip = 0
        
        # Get messages from MongoDB
        messages = await mongodb_service.get_chat_history(
            session_id=session_id,
            limit=limit,
            skip=skip
        )
        
        # Get total count
        total_count = await mongodb_service.get_message_count(session_id)
        
        return {
            "session_id": session_id,
            "messages": messages,
            "total_count": total_count,
            "returned_count": len(messages),
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )


@router.delete("/history/{session_id}", status_code=204)
async def delete_chat_history(session_id: str):
    """
    Delete all chat history for a session from MongoDB.
    
    **Args:**
    - **session_id**: Session identifier
    
    **Warning:** This action cannot be undone!
    """
    try:
        deleted_count = await mongodb_service.delete_session_chats(session_id)
        
        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="No chat history found for this session"
            )
        
        return {"message": f"Deleted {deleted_count} messages"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chat history: {str(e)}"
        )


def _get_current_day_title(result: dict) -> str:
    """Helper to extract current day title from lesson plan."""
    lesson_plan = result.get("lesson_plan", {})
    current_day = result.get("current_day", 1)
    
    if not lesson_plan or "days" not in lesson_plan:
        return "General Learning"
    
    day_data = next(
        (day for day in lesson_plan["days"] if day["day"] == current_day),
        {}
    )
    
    return day_data.get("title", f"Day {current_day}")


def _get_lesson_plan_summary(lesson_plan: dict) -> dict:
    """Helper to create a summary of the lesson plan (without full details)."""
    if not lesson_plan:
        return {}
    
    return {
        "topic": lesson_plan.get("topic"),
        "total_days": lesson_plan.get("total_days", 0),
        "days_count": len(lesson_plan.get("days", [])),
        "has_objectives": any(day.get("learning_objectives") for day in lesson_plan.get("days", []))
    }

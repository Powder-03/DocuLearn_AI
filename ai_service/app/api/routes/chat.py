"""
Chat endpoints for AI tutor interactions
Full async REST API implementation
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
from app.api.deps import get_db
from langchain_core.messages import HumanMessage

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
        # Get session state from database
        session_data = get_session_state(request.session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Add user message to chat history
        current_history = session_data.get("chat_history", [])
        current_history.append(HumanMessage(content=request.message))
        
        # Prepare graph state
        graph_state = {
            "session_id": request.session_id,
            "user_id": session_data["user_id"],
            "topic": session_data["topic"],
            "lesson_plan": session_data.get("lesson_plan"),
            "current_day": session_data.get("current_day", 1),
            "chat_history": current_history,
            "total_days": session_data.get("total_days", 7),
            "time_per_day": session_data.get("time_per_day", "30 minutes")
        }
        
        # Invoke graph asynchronously
        config = {"configurable": {"thread_id": request.session_id}}
        result = await generation_app.ainvoke(graph_state, config=config)
        
        # Extract AI response
        ai_message = result["chat_history"][-1]
        
        # Get current day info
        day_title = _get_current_day_title(result)
        
        return ChatResponse(
            session_id=request.session_id,
            message=ai_message.content,
            current_day=result.get("current_day", 1),
            lesson_plan_exists=result.get("lesson_plan") is not None,
            metadata={
                "day_title": day_title,
                "total_days": result.get("lesson_plan", {}).get("total_days", 0) if result.get("lesson_plan") else 0,
                "message_count": len(result.get("chat_history", []))
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
            # Get session state
            session_data = get_session_state(request.session_id)
            
            if not session_data:
                yield f"data: {json.dumps({'event': 'error', 'data': 'Session not found'})}\n\n"
                return
            
            # Add user message to history
            current_history = session_data.get("chat_history", [])
            current_history.append(HumanMessage(content=request.message))
            
            # Prepare graph state
            graph_state = {
                "session_id": request.session_id,
                "user_id": session_data["user_id"],
                "topic": session_data["topic"],
                "lesson_plan": session_data.get("lesson_plan"),
                "current_day": session_data.get("current_day", 1),
                "chat_history": current_history,
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
            
            # Send completion event
            yield f"data: {json.dumps({
                'event': 'done',
                'data': 'Stream complete',
                'metadata': {
                    'total_chars': len(full_response),
                    'current_day': session_data.get('current_day', 1)
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
    - Total message count
    - Next node to execute (for debugging)
    - Full metadata (topic, plan, etc.)
    """
    try:
        # Try to get state from graph checkpointer first
        config = {"configurable": {"thread_id": session_id}}
        state_snapshot = generation_app.get_state(config)
        
        if state_snapshot and state_snapshot.values:
            state_values = state_snapshot.values
            
            return GraphStateResponse(
                session_id=session_id,
                current_day=state_values.get("current_day", 1),
                lesson_plan_exists=state_values.get("lesson_plan") is not None,
                total_messages=len(state_values.get("chat_history", [])),
                next_node=state_snapshot.next[0] if state_snapshot.next else None,
                metadata={
                    "topic": state_values.get("topic"),
                    "total_days": state_values.get("total_days", 0),
                    "time_per_day": state_values.get("time_per_day"),
                    "lesson_plan_summary": _get_lesson_plan_summary(state_values.get("lesson_plan"))
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
            total_messages=len(session_data.get("chat_history", [])),
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

"""
Chat service - Business logic for chat interactions
Handles message processing, history management, and AI responses
"""
from typing import Dict, Any, List, AsyncIterator, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from app.services.memory import get_session_state
from app.services.mongodb import mongodb_service
from app.graphs.generation_graph import generation_app


class ChatService:
    """Service for handling chat operations"""
    
    # ========== Public Methods ==========
    
    async def process_chat_message(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Process a chat message and return AI response.
        
        Args:
            session_id: Session identifier
            message: User's message
            
        Returns:
            Dictionary with AI response and metadata
            
        Raises:
            ValueError: If session not found
        """
        # 1. Validate and get session
        session_data = self._get_session_or_raise(session_id)
        
        # 2. Save user message
        await self._save_user_message(session_id, session_data["user_id"], message, session_data)
        
        # 3. Get chat history
        chat_history = await self._get_langchain_chat_history(session_id)
        
        # 4. Build graph state
        graph_state = self._build_graph_state(session_id, session_data, chat_history)
        
        # 5. Invoke graph
        result = await self._invoke_graph(session_id, graph_state)
        
        # 6. Extract AI message
        ai_message = self._extract_ai_message(result)
        
        # 7. Save AI response
        await self._save_ai_message(
            session_id,
            session_data["user_id"],
            ai_message.content,
            result
        )
        
        # 8. Build response
        return await self._build_chat_response(session_id, ai_message.content, result)
    
    async def stream_chat_message(
        self,
        session_id: str,
        message: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream chat message response.
        
        Args:
            session_id: Session identifier
            message: User's message
            
        Yields:
            Chunks of the response
        """
        try:
            # 1. Validate and get session
            session_data = self._get_session_or_raise(session_id)
            
            # 2. Save user message
            await self._save_user_message(session_id, session_data["user_id"], message, session_data)
            
            # 3. Get chat history
            chat_history = await self._get_langchain_chat_history(session_id)
            
            # 4. Build graph state
            graph_state = self._build_graph_state(session_id, session_data, chat_history)
            
            # 5. Start streaming
            yield {"event": "start", "data": "Generating response..."}
            
            # 6. Stream chunks
            full_response = ""
            async for chunk_data in self._stream_graph_response(session_id, graph_state):
                if chunk_data.get("event") == "token":
                    full_response += chunk_data["data"]
                yield chunk_data
            
            # 7. Save AI response
            await self._save_ai_message(
                session_id,
                session_data["user_id"],
                full_response,
                {"current_day": session_data.get("current_day", 1)}
            )
            
            # 8. Send completion
            total_messages = await mongodb_service.get_message_count(session_id)
            yield {
                "event": "done",
                "data": "Stream complete",
                "metadata": {
                    "total_chars": len(full_response),
                    "current_day": session_data.get("current_day", 1),
                    "total_messages": total_messages
                }
            }
            
        except ValueError as e:
            yield {"event": "error", "data": str(e)}
        except Exception as e:
            yield {"event": "error", "data": f"Streaming error: {str(e)}"}
    
    async def get_graph_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get current graph state for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Graph state dictionary
            
        Raises:
            ValueError: If session not found
        """
        # Try graph checkpointer first
        config = {"configurable": {"thread_id": session_id}}
        state_snapshot = generation_app.get_state(config)
        
        total_messages = await mongodb_service.get_message_count(session_id)
        
        if state_snapshot and state_snapshot.values:
            return self._build_graph_state_response(
                session_id,
                state_snapshot.values,
                total_messages,
                state_snapshot.next[0] if state_snapshot.next else None,
                source="graph_checkpointer"
            )
        
        # Fallback to database
        session_data = self._get_session_or_raise(session_id)
        
        return self._build_graph_state_response(
            session_id,
            session_data,
            total_messages,
            None,
            source="database"
        )
    
    async def get_chat_history(
        self,
        session_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """Get paginated chat history."""
        messages = await mongodb_service.get_messages(
            session_id=session_id,
            limit=limit,
            skip=skip
        )
        
        total_count = await mongodb_service.get_message_count(session_id)
        
        return {
            "session_id": session_id,
            "messages": messages,
            "total": total_count,
            "limit": limit,
            "skip": skip,
            "has_more": (skip + len(messages)) < total_count
        }
    
    async def delete_chat_history(self, session_id: str) -> int:
        """Delete all chat history for a session."""
        return await mongodb_service.delete_session_chats(session_id)
    
    # ========== Private Helper Methods ==========
    
    def _get_session_or_raise(self, session_id: str) -> Dict[str, Any]:
        """Get session data or raise ValueError."""
        session_data = get_session_state(session_id)
        if not session_data:
            raise ValueError("Session not found")
        return session_data
    
    async def _save_user_message(
        self,
        session_id: str,
        user_id: str,
        message: str,
        session_data: Dict[str, Any]
    ) -> None:
        """Save user message to MongoDB."""
        await mongodb_service.save_message(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=message,
            metadata={"current_day": session_data.get("current_day", 1)}
        )
    
    async def _save_ai_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        result: Dict[str, Any]
    ) -> None:
        """Save AI response to MongoDB."""
        await mongodb_service.save_message(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=content,
            metadata={
                "current_day": result.get("current_day", 1),
                "lesson_plan_exists": result.get("lesson_plan") is not None
            }
        )
    
    async def _get_langchain_chat_history(
        self,
        session_id: str,
        count: int = 20
    ) -> List[BaseMessage]:
        """Get chat history from MongoDB in LangChain format."""
        recent_messages = await mongodb_service.get_recent_messages(
            session_id=session_id,
            count=count
        )
        
        chat_history = []
        for msg in recent_messages:
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            else:
                chat_history.append(AIMessage(content=msg["content"]))
        
        return chat_history
    
    def _build_graph_state(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        chat_history: List[BaseMessage]
    ) -> Dict[str, Any]:
        """Build graph state from session data and chat history."""
        return {
            "session_id": session_id,
            "user_id": session_data["user_id"],
            "topic": session_data["topic"],
            "lesson_plan": session_data.get("lesson_plan"),
            "current_day": session_data.get("current_day", 1),
            "chat_history": chat_history,
            "total_days": session_data.get("total_days", 7),
            "time_per_day": session_data.get("time_per_day", "30 minutes")
        }
    
    async def _invoke_graph(
        self,
        session_id: str,
        graph_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke the LangGraph."""
        config = {"configurable": {"thread_id": session_id}}
        return await generation_app.ainvoke(graph_state, config=config)
    
    async def _stream_graph_response(
        self,
        session_id: str,
        graph_state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream graph response chunks."""
        config = {"configurable": {"thread_id": session_id}}
        full_response = ""
        
        async for chunk in generation_app.astream(graph_state, config=config):
            if "chat_history" in chunk and chunk["chat_history"]:
                message = chunk["chat_history"][-1]
                
                if hasattr(message, 'content') and message.content:
                    content_chunk = message.content[len(full_response):]
                    full_response = message.content
                    
                    if content_chunk:
                        yield {
                            "event": "token",
                            "data": content_chunk,
                            "metadata": {
                                "current_day": chunk.get("current_day", 1),
                                "progress": len(full_response)
                            }
                        }
    
    def _extract_ai_message(self, result: Dict[str, Any]) -> BaseMessage:
        """Extract AI message from graph result."""
        return result["chat_history"][-1]
    
    async def _build_chat_response(
        self,
        session_id: str,
        message: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build chat response dictionary."""
        total_messages = await mongodb_service.get_message_count(session_id)
        
        return {
            "session_id": session_id,
            "message": message,
            "current_day": result.get("current_day", 1),
            "lesson_plan_exists": result.get("lesson_plan") is not None,
            "metadata": {
                "day_title": self._get_current_day_title(result),
                "total_days": self._get_total_days(result),
                "message_count": total_messages
            }
        }
    
    def _build_graph_state_response(
        self,
        session_id: str,
        state_values: Dict[str, Any],
        total_messages: int,
        next_node: Optional[str],
        source: str
    ) -> Dict[str, Any]:
        """Build graph state response."""
        return {
            "session_id": session_id,
            "current_day": state_values.get("current_day", 1),
            "lesson_plan_exists": state_values.get("lesson_plan") is not None,
            "total_messages": total_messages,
            "next_node": next_node,
            "metadata": {
                "topic": state_values.get("topic"),
                "total_days": state_values.get("total_days", 0),
                "time_per_day": state_values.get("time_per_day"),
                "lesson_plan_summary": self._get_lesson_plan_summary(
                    state_values.get("lesson_plan")
                ),
                "source": source
            }
        }
    
    def _get_current_day_title(self, result: Dict[str, Any]) -> str:
        """Extract current day title from lesson plan."""
        lesson_plan = result.get("lesson_plan", {})
        current_day = result.get("current_day", 1)
        
        if not lesson_plan or "days" not in lesson_plan:
            return "General Learning"
        
        day_data = next(
            (day for day in lesson_plan["days"] if day["day"] == current_day),
            {}
        )
        
        return day_data.get("title", f"Day {current_day}")
    
    def _get_total_days(self, result: Dict[str, Any]) -> int:
        """Get total days from result."""
        lesson_plan = result.get("lesson_plan")
        if lesson_plan:
            return lesson_plan.get("total_days", 0)
        return 0
    
    def _get_lesson_plan_summary(self, lesson_plan: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of the lesson plan."""
        if not lesson_plan:
            return {}
        
        return {
            "topic": lesson_plan.get("topic"),
            "total_days": lesson_plan.get("total_days", 0),
            "days_count": len(lesson_plan.get("days", [])),
            "has_objectives": any(
                day.get("learning_objectives")
                for day in lesson_plan.get("days", [])
            )
        }


# Export singleton instance
chat_service = ChatService()

import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from langchain_core.messages import messages_to_dict, messages_from_dict

from app.db.session import SessionLocal
from app.db.models import LearningSession


def get_session_state(db: Session, session_id: str) -> Dict[str, Any]:
    """
    Retrieve the current state of a learning session from the database.
    
    Args:
        db: The SQLAlchemy database session.
        session_id: UUID string identifying the session
        
    Returns:
        Dictionary containing all state fields compatible with GenerationGraphState
        
    Raises:
        ValueError: If session_id is not found
    """
    try:
        # Convert session_id to UUID if needed
        try:
            session_uuid = uuid.UUID(session_id)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid session_id format: {session_id}")
        
        # Query for the session
        session = db.query(LearningSession).filter(
            LearningSession.session_id == session_uuid
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Convert chat_history from JSONB to BaseMessage objects
        chat_history = []
        if session.chat_history:
            chat_history = messages_from_dict(session.chat_history)
        
        # Build state dictionary
        state = {
            "session_id": str(session.session_id),
            "user_id": str(session.user_id),
            "topic": session.topic or "",
            "total_days": session.lesson_plan.get("total_days", 0) if session.lesson_plan else 0,
            "time_per_day": session.lesson_plan.get("time_per_day", "") if session.lesson_plan else "",
            "lesson_plan": session.lesson_plan,
            "current_day": session.current_day,
            "chat_history": chat_history,
            "memory_summary": session.memory_summary
        }
        
        return state
        
    except Exception as e:
        # Re-raise exceptions to be handled by the caller
        raise e


def update_session_state(db: Session, session_id: str, updates: Dict[str, Any]) -> None:
    """
    Update specific fields of a learning session in the database.
    
    Args:
        db: The SQLAlchemy database session.
        session_id: UUID string identifying the session
        updates: Dictionary of fields to update
        
    Raises:
        ValueError: If session_id is not found
    """
    try:
        # Convert session_id to UUID if needed
        try:
            session_uuid = uuid.UUID(session_id)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid session_id format: {session_id}")
        
        # Query for the session
        session = db.query(LearningSession).filter(
            LearningSession.session_id == session_uuid
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Process updates
        for key, value in updates.items():
            # Special handling for chat_history - convert to dict format
            if key == "chat_history" and value is not None:
                value = messages_to_dict(value)
            
            # Update the attribute
            if hasattr(session, key):
                setattr(session, key, value)
        
        # Commit changes
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise e


def create_session(
    db: Session,
    session_id: str,
    user_id: str,
    topic: str,
    total_days: int,
    time_per_day: str
) -> Dict[str, Any]:
    """
    Create a new learning session in the database.
    
    Args:
        db: The SQLAlchemy database session.
        session_id: UUID string for the new session
        user_id: UUID string or regular string identifying the user
        topic: The learning topic
        total_days: Number of days in the learning plan
        time_per_day: Time commitment per day (e.g., "30 minutes")
        
    Returns:
        Dictionary containing the created session state
    """
    try:
        # Convert user_id to UUID if it's not already one
        try:
            user_uuid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            # If user_id is not a valid UUID, generate one based on the string
            user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
        
        # Create new session
        new_session = LearningSession(
            session_id=uuid.UUID(session_id),
            user_id=user_uuid,
            mode="generation",
            topic=topic,
            lesson_plan=None,  # Will be created by plan_generator_node
            chat_history=[],
            memory_summary=None,
            current_day=1,
            total_days=total_days,
            time_per_day=time_per_day
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        # Return initial state
        return {
            "session_id": str(new_session.session_id),
            "user_id": str(new_session.user_id),
            "topic": new_session.topic,
            "total_days": total_days,
            "time_per_day": time_per_day,
            "lesson_plan": None,
            "current_day": 1,
            "chat_history": []
        }
        
    except Exception as e:
        db.rollback()
        raise e

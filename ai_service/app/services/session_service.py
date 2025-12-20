"""
Session Service - Handles all business logic for learning sessions
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import LearningSession
from app.services.memory import create_session as create_session_state


class SessionService:
    """Service for managing learning sessions"""
    
    def create_session(
        self,
        db: Session,
        user_id: str,
        topic: str,
        total_days: int = 7,
        time_per_day: str = "30 minutes"
    ) -> Dict[str, Any]:
        """
        Create a new learning session with state management
        
        Args:
            db: The SQLAlchemy database session.
            user_id: User identifier
            topic: Learning topic
            total_days: Total days for the learning plan
            time_per_day: Time commitment per day
            
        Returns:
            Dict with session details
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If session creation fails
        """
        # Validation
        if not user_id or not user_id.strip():
            raise ValueError("User ID is required")
        
        if not topic or not topic.strip():
            raise ValueError("Topic is required")
        
        if total_days < 1 or total_days > 365:
            raise ValueError("Total days must be between 1 and 365")
        
        try:
            # Generate a unique session ID
            import uuid
            session_id = str(uuid.uuid4())
            
            # Create session state (PostgreSQL + in-memory)
            create_session_state(
                db=db,
                session_id=session_id,
                user_id=user_id,
                topic=topic,
                total_days=total_days,
                time_per_day=time_per_day
            )
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "topic": topic,
                "total_days": total_days,
                "time_per_day": time_per_day,
                "current_day": 1,
                "has_lesson_plan": False,
                "message_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "message": "Session created successfully"
            }
            
        except IntegrityError as e:
            raise RuntimeError(f"Database error: Session might already exist - {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to create session: {str(e)}")
    
    
    def get_session(self, db: Session, session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get session details by ID
        
        Args:
            db: The SQLAlchemy database session.
            session_id: Session identifier
            user_id: Optional user ID for authorization check
            
        Returns:
            Session details or None if not found
            
        Raises:
            PermissionError: If user_id provided and doesn't match session owner
        """
        session = db.query(LearningSession).filter(
            LearningSession.session_id == session_id
        ).first()
        
        if not session:
            return None
        
        # Authorization check if user_id provided
        if user_id and str(session.user_id) != user_id:
            raise PermissionError("You don't have permission to access this session")
        
        # Count messages in chat history
        # This relationship is not loaded by default, it will trigger a lazy load
        # For high performance, consider a separate query or a back-populating counter
        # message_count = len(session.chat_history) if session.chat_history else 0
        message_count = 0 # Placeholder to avoid N+1 query problem in a sync function
        
        return {
            "session_id": str(session.session_id),
            "user_id": str(session.user_id),
            "topic": session.topic,
            "total_days": session.total_days if hasattr(session, 'total_days') else (session.lesson_plan.get('total_days', 7) if session.lesson_plan else 7),
            "current_day": session.current_day,
            "has_lesson_plan": session.lesson_plan is not None,
            "message_count": message_count,
            "created_at": session.created_at.isoformat() if session.created_at else None
        }
    
    
    def list_user_sessions(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        include_completed: bool = True
    ) -> Dict[str, Any]:
        """
        List all sessions for a user
        
        Args:
            db: The SQLAlchemy database session.
            user_id: User identifier
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            include_completed: Whether to include completed sessions
            
        Returns:
            Dict with sessions list and metadata
        """
        # Convert user_id to UUID if needed
        import uuid
        try:
            user_uuid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            # If user_id is not a valid UUID, generate one based on the string
            user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, user_id)
        
        query = db.query(LearningSession).filter(
            LearningSession.user_id == user_uuid
        )
        
        # Filter completed sessions if needed
        if not include_completed:
            query = query.filter(
                LearningSession.current_day < LearningSession.total_days
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        sessions = query.order_by(
            LearningSession.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "sessions": [
                {
                    "session_id": str(s.session_id),
                    "topic": s.topic,
                    "current_day": s.current_day,
                    "total_days": s.total_days,
                    "time_per_day": s.time_per_day,
                    "is_completed": s.current_day >= s.total_days,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None
                }
                for s in sessions
            ]
        }
    
    
    def update_session_progress(
        self,
        db: Session,
        session_id: str,
        user_id: Optional[str] = None,
        increment_day: bool = True
    ) -> Dict[str, Any]:
        """
        Update session progress (advance to next day)
        
        Args:
            db: The SQLAlchemy database session.
            session_id: Session identifier
            user_id: Optional user ID for authorization
            increment_day: Whether to increment the current day
            
        Returns:
            Updated session details
            
        Raises:
            ValueError: If session not found
            PermissionError: If user doesn't own the session
            RuntimeError: If session is already completed
        """
        try:
            session = db.query(LearningSession).filter(
                LearningSession.session_id == session_id
            ).first()
            
            if not session:
                raise ValueError("Session not found")
            
            # Authorization check
            if user_id and session.user_id != user_id:
                raise PermissionError("You don't have permission to modify this session")
            
            # Check if already completed
            if session.current_day >= session.total_days:
                raise RuntimeError("Session is already completed")
            
            # Update progress
            if increment_day:
                session.current_day += 1
                session.updated_at = datetime.utcnow()
                db.commit()
            
            return {
                "session_id": session.session_id,
                "current_day": session.current_day,
                "total_days": session.total_days,
                "is_completed": session.current_day >= session.total_days,
                "message": f"Progress updated to day {session.current_day}"
            }
            
        except Exception as e:
            db.rollback()
            raise
    
    
    def delete_session(
        self,
        db: Session,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Delete a session and all associated data
        
        Args:
            db: The SQLAlchemy database session.
            session_id: Session identifier
            user_id: Optional user ID for authorization
            
        Returns:
            Confirmation message
            
        Raises:
            ValueError: If session not found
            PermissionError: If user doesn't own the session
        """
        try:
            session = db.query(LearningSession).filter(
                LearningSession.session_id == session_id
            ).first()
            
            if not session:
                raise ValueError("Session not found")
            
            # Authorization check
            if user_id and session.user_id != user_id:
                raise PermissionError("You don't have permission to delete this session")
            
            # Delete from database
            db.delete(session)
            db.commit()
            
            # Note: Chat history deletion handled separately by chat_service
            
            return {
                "message": "Session deleted successfully",
                "session_id": session_id
            }
            
        except Exception as e:
            db.rollback()
            raise
    
    
    def get_session_statistics(self, db: Session, user_id: str) -> Dict[str, Any]:
        """
        Get learning statistics for a user
        
        Args:
            db: The SQLAlchemy database session.
            user_id: User identifier
            
        Returns:
            Statistics about user's learning sessions
        """
        sessions = db.query(LearningSession).filter(
            LearningSession.user_id == user_id
        ).all()
        
        total_sessions = len(sessions)
        completed_sessions = sum(1 for s in sessions if s.current_day >= s.total_days)
        in_progress_sessions = total_sessions - completed_sessions
        
        total_days_planned = sum(s.total_days for s in sessions)
        total_days_completed = sum(
            min(s.current_day, s.total_days) for s in sessions
        )
        
        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "in_progress_sessions": in_progress_sessions,
            "total_days_planned": total_days_planned,
            "total_days_completed": total_days_completed,
            "completion_rate": (
                (completed_sessions / total_sessions * 100) 
                if total_sessions > 0 else 0
            )
        }


# Singleton instance
session_service = SessionService()

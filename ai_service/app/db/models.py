import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, UUID, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


Base = declarative_base()


class LearningSession(Base):
    """
    Model for storing learning session state and history.
    This table persists all state for the Generation Mode graph.
    """
    __tablename__ = "learning_sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    mode = Column(String, default="generation", nullable=False)
    topic = Column(String, nullable=True)
    total_days = Column(Integer, default=7, nullable=False)
    time_per_day = Column(String, default="30 minutes", nullable=False)
    lesson_plan = Column(JSONB, nullable=True)
    chat_history = Column(JSONB, nullable=True)  # Stores List[Dict] representation of messages
    memory_summary = Column(Text, nullable=True)
    current_day = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Index for querying by user_id
    __table_args__ = (
        Index('ix_learning_sessions_user_id', 'user_id'),
    )

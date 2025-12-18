"""
MongoDB service for chat history storage
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


class MongoDBService:
    """MongoDB service for chat operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.chats_collection = None
        self.sessions_collection = None
        
    async def connect(self):
        """Connect to MongoDB"""
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            raise ValueError("MONGODB_URL not set in environment")
        
        logger.info(f"Connecting to MongoDB...")
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client.get_default_database()
        self.chats_collection = self.db.chats
        self.sessions_collection = self.db.sessions
        
        # Create indexes
        await self._create_indexes()
        logger.info("✅ MongoDB connected successfully")
        
    async def _create_indexes(self):
        """Create necessary indexes for optimal query performance"""
        # Chat collection indexes
        await self.chats_collection.create_index([("session_id", ASCENDING)])
        await self.chats_collection.create_index([("user_id", ASCENDING)])
        await self.chats_collection.create_index([("created_at", DESCENDING)])
        await self.chats_collection.create_index([
            ("session_id", ASCENDING),
            ("created_at", ASCENDING)
        ])
        
        # Session collection indexes
        await self.sessions_collection.create_index([("session_id", ASCENDING)], unique=True)
        await self.sessions_collection.create_index([("user_id", ASCENDING)])
        
        logger.info("✅ MongoDB indexes created")
        
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def close(self):
        """Alias for disconnect"""
        await self.disconnect()
    
    async def save_message(
        self,
        session_id: str,
        user_id: str,
        role: str,  # "user" or "assistant"
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a single chat message
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            role: Message role ("user" or "assistant")
            content: Message content
            metadata: Additional metadata
            
        Returns:
            Message ID as string
        """
        message = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.chats_collection.insert_one(message)
        logger.debug(f"Message saved: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def save_messages_batch(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Save multiple messages in a single operation
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of inserted message IDs
        """
        if not messages:
            return []
        
        # Add timestamps
        for msg in messages:
            msg["created_at"] = datetime.utcnow()
            msg["updated_at"] = datetime.utcnow()
        
        result = await self.chats_collection.insert_many(messages)
        logger.debug(f"Batch of {len(messages)} messages saved")
        return [str(id) for id in result.inserted_ids]
    
    async def get_chat_history(
        self,
        session_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a session with pagination
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            skip: Number of messages to skip
            
        Returns:
            List of messages in chronological order
        """
        cursor = self.chats_collection.find(
            {"session_id": session_id}
        ).sort("created_at", ASCENDING).skip(skip).limit(limit)
        
        messages = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for msg in messages:
            msg["_id"] = str(msg["_id"])
            
        return messages
    
    async def get_recent_messages(
        self,
        session_id: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most recent messages for a session
        
        Args:
            session_id: Session identifier
            count: Number of recent messages to return
            
        Returns:
            List of messages in chronological order (oldest to newest)
        """
        cursor = self.chats_collection.find(
            {"session_id": session_id}
        ).sort("created_at", DESCENDING).limit(count)
        
        messages = await cursor.to_list(length=count)
        messages.reverse()  # Return in chronological order
        
        for msg in messages:
            msg["_id"] = str(msg["_id"])
            
        return messages
    
    async def get_message_count(self, session_id: str) -> int:
        """
        Get total message count for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Total number of messages
        """
        return await self.chats_collection.count_documents(
            {"session_id": session_id}
        )
    
    async def delete_session_chats(self, session_id: str) -> int:
        """
        Delete all chats for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of deleted messages
        """
        result = await self.chats_collection.delete_many(
            {"session_id": session_id}
        )
        logger.info(f"Deleted {result.deleted_count} messages for session {session_id}")
        return result.deleted_count
    
    async def delete_old_messages(self, days: int = 90) -> int:
        """
        Delete messages older than specified days
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted messages
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.chats_collection.delete_many(
            {"created_at": {"$lt": cutoff_date}}
        )
        logger.info(f"Deleted {result.deleted_count} old messages")
        return result.deleted_count
    
    async def get_user_chat_sessions(
        self,
        user_id: str,
        limit: int = 20
    ) -> List[str]:
        """
        Get all session IDs where user has chatted
        
        Args:
            user_id: User identifier
            limit: Maximum number of sessions
            
        Returns:
            List of session IDs
        """
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$session_id"}},
            {"$sort": {"_id": DESCENDING}},
            {"$limit": limit}
        ]
        
        cursor = self.chats_collection.aggregate(pipeline)
        sessions = await cursor.to_list(length=limit)
        
        return [s["_id"] for s in sessions]
    
    async def search_messages(
        self,
        session_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search messages by content
        
        Args:
            session_id: Session identifier
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching messages
        """
        cursor = self.chats_collection.find({
            "session_id": session_id,
            "content": {"$regex": query, "$options": "i"}
        }).limit(limit)
        
        messages = await cursor.to_list(length=limit)
        
        for msg in messages:
            msg["_id"] = str(msg["_id"])
            
        return messages
    
    async def update_session_metadata(
        self,
        session_id: str,
        metadata: Dict[str, Any]
    ):
        """
        Update or create session metadata
        
        Args:
            session_id: Session identifier
            metadata: Metadata to store
        """
        await self.sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    **metadata,
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    async def get_session_metadata(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get session metadata
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session metadata or None
        """
        session = await self.sessions_collection.find_one(
            {"session_id": session_id}
        )
        
        if session:
            session["_id"] = str(session["_id"])
            
        return session


# Global instance
mongodb_service = MongoDBService()


async def get_mongodb() -> MongoDBService:
    """Dependency for FastAPI"""
    return mongodb_service

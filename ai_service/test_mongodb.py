"""
Test MongoDB chat storage integration
Run after starting the services with docker-compose
"""
import asyncio
from app.services.mongodb import mongodb_service
import os

# Set environment variable for testing
os.environ["MONGODB_URL"] = "mongodb://admin:supersecret@localhost:27017/learning_saas_chats?authSource=admin"


async def test_mongodb():
    """Test MongoDB operations"""
    print("🧪 Testing MongoDB Integration")
    print("=" * 60)
    
    try:
        # Connect
        print("\n1️⃣ Connecting to MongoDB...")
        await mongodb_service.connect()
        print("✅ Connected successfully")
        
        # Test session ID
        test_session_id = "test-session-123"
        test_user_id = "test-user-456"
        
        # Save user message
        print("\n2️⃣ Saving user message...")
        msg_id = await mongodb_service.save_message(
            session_id=test_session_id,
            user_id=test_user_id,
            role="user",
            content="Hello! Can you teach me Python?",
            metadata={"current_day": 1}
        )
        print(f"✅ User message saved with ID: {msg_id}")
        
        # Save AI response
        print("\n3️⃣ Saving AI response...")
        ai_msg_id = await mongodb_service.save_message(
            session_id=test_session_id,
            user_id=test_user_id,
            role="assistant",
            content="Of course! Python is a great language to start with. What would you like to learn first?",
            metadata={"current_day": 1}
        )
        print(f"✅ AI message saved with ID: {ai_msg_id}")
        
        # Get message count
        print("\n4️⃣ Getting message count...")
        count = await mongodb_service.get_message_count(test_session_id)
        print(f"✅ Total messages: {count}")
        
        # Get chat history
        print("\n5️⃣ Retrieving chat history...")
        history = await mongodb_service.get_chat_history(test_session_id)
        print(f"✅ Retrieved {len(history)} messages:")
        for i, msg in enumerate(history, 1):
            print(f"   {i}. [{msg['role']}]: {msg['content'][:50]}...")
        
        # Get recent messages
        print("\n6️⃣ Getting recent messages...")
        recent = await mongodb_service.get_recent_messages(test_session_id, count=5)
        print(f"✅ Retrieved {len(recent)} recent messages")
        
        # Save batch
        print("\n7️⃣ Testing batch save...")
        batch_messages = [
            {
                "session_id": test_session_id,
                "user_id": test_user_id,
                "role": "user",
                "content": "What are variables?",
                "metadata": {"current_day": 1}
            },
            {
                "session_id": test_session_id,
                "user_id": test_user_id,
                "role": "assistant",
                "content": "Variables are containers for storing data values.",
                "metadata": {"current_day": 1}
            }
        ]
        ids = await mongodb_service.save_messages_batch(batch_messages)
        print(f"✅ Batch saved: {len(ids)} messages")
        
        # Final count
        final_count = await mongodb_service.get_message_count(test_session_id)
        print(f"\n📊 Final message count: {final_count}")
        
        # Search messages
        print("\n8️⃣ Testing search...")
        results = await mongodb_service.search_messages(
            session_id=test_session_id,
            query="Python",
            limit=5
        )
        print(f"✅ Found {len(results)} messages containing 'Python'")
        
        # Update session metadata
        print("\n9️⃣ Updating session metadata...")
        await mongodb_service.update_session_metadata(
            session_id=test_session_id,
            metadata={
                "user_id": test_user_id,
                "topic": "Python Programming",
                "total_days": 7,
                "current_day": 1
            }
        )
        print("✅ Session metadata updated")
        
        # Get session metadata
        print("\n🔟 Retrieving session metadata...")
        metadata = await mongodb_service.get_session_metadata(test_session_id)
        print(f"✅ Metadata: {metadata.get('topic')} - Day {metadata.get('current_day')}/{metadata.get('total_days')}")
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        deleted = await mongodb_service.delete_session_chats(test_session_id)
        print(f"✅ Deleted {deleted} test messages")
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await mongodb_service.disconnect()
        print("\n👋 MongoDB connection closed")


if __name__ == "__main__":
    asyncio.run(test_mongodb())

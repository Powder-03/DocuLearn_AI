"""
Live API Testing Script
Tests all endpoints when the service is running
Usage: python test_api_live.py
"""
import requests
import json
import time
from typing import Optional

BASE_URL = "http://localhost:8001/api/v1"
session_id: Optional[str] = None


def test_health():
    """Test health endpoints"""
    print("\n🏥 Testing Health Endpoints")
    print("=" * 60)
    
    # Test root health
    response = requests.get(f"{BASE_URL}/")
    print(f"✅ GET / - Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test detailed health
    response = requests.get(f"{BASE_URL}/health")
    print(f"✅ GET /health - Status: {response.status_code}")
    print(f"   Response: {response.json()}")


def test_create_session():
    """Test session creation"""
    global session_id
    
    print("\n📝 Testing Session Creation")
    print("=" * 60)
    
    payload = {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "topic": "Python Programming Basics",
        "total_days": 5,
        "time_per_day": "30 minutes"
    }
    
    response = requests.post(f"{BASE_URL}/sessions/create", json=payload)
    print(f"✅ POST /sessions/create - Status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        session_id = data["session_id"]
        print(f"   Session ID: {session_id}")
        print(f"   Topic: {data['topic']}")
        print(f"   Total Days: {data['total_days']}")
    else:
        print(f"   Error: {response.text}")


def test_get_session():
    """Test getting session details"""
    if not session_id:
        print("⚠️  Skipping session tests - no session created")
        return
    
    print("\n🔍 Testing Get Session")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    print(f"✅ GET /sessions/{session_id} - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Topic: {data['topic']}")
        print(f"   Current Day: {data['current_day']}/{data['total_days']}")
        print(f"   Has Lesson Plan: {data['has_lesson_plan']}")
        print(f"   Message Count: {data['message_count']}")


def test_get_lesson_plan():
    """Test getting lesson plan"""
    if not session_id:
        print("⚠️  Skipping lesson plan test - no session created")
        return
    
    print("\n📚 Testing Get Lesson Plan")
    print("=" * 60)
    
    # Wait a bit for lesson plan generation
    print("   Waiting 2 seconds for lesson plan generation...")
    time.sleep(2)
    
    response = requests.get(f"{BASE_URL}/sessions/{session_id}/lesson-plan")
    print(f"✅ GET /sessions/{session_id}/lesson-plan - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        lesson_plan = data.get("lesson_plan", {})
        print(f"   Current Day: {data.get('current_day')}")
        if lesson_plan:
            print(f"   Plan Topic: {lesson_plan.get('topic')}")
            print(f"   Total Days: {lesson_plan.get('total_days')}")
            days = lesson_plan.get('days', [])
            print(f"   Days in Plan: {len(days)}")
    else:
        print(f"   Note: {response.json().get('detail')}")


def test_chat_invoke():
    """Test synchronous chat"""
    if not session_id:
        print("⚠️  Skipping chat test - no session created")
        return
    
    print("\n💬 Testing Chat Invoke (Synchronous)")
    print("=" * 60)
    
    payload = {
        "session_id": session_id,
        "message": "Hello! Can you explain what we'll learn in this course?"
    }
    
    response = requests.post(f"{BASE_URL}/chat/invoke", json=payload)
    print(f"✅ POST /chat/invoke - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Current Day: {data.get('current_day')}")
        print(f"   Lesson Plan Exists: {data.get('lesson_plan_exists')}")
        print(f"   Response Preview: {data.get('message', '')[:100]}...")
        print(f"   Metadata: {data.get('metadata')}")


def test_chat_stream():
    """Test streaming chat"""
    if not session_id:
        print("⚠️  Skipping stream test - no session created")
        return
    
    print("\n🌊 Testing Chat Stream (SSE)")
    print("=" * 60)
    
    payload = {
        "session_id": session_id,
        "message": "What's the first thing I should learn?"
    }
    
    print("✅ POST /chat/stream - Streaming response:")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/stream",
            json=payload,
            stream=True,
            timeout=30
        )
        
        event_count = 0
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    event_count += 1
                    data = json.loads(line_str[6:])
                    event_type = data.get('event', 'unknown')
                    
                    if event_type == 'start':
                        print(f"   🚀 Stream started")
                    elif event_type == 'token':
                        print(".", end="", flush=True)
                    elif event_type == 'done':
                        print(f"\n   ✅ Stream completed ({event_count} events)")
                    elif event_type == 'error':
                        print(f"\n   ❌ Error: {data.get('data')}")
        
    except Exception as e:
        print(f"   ⚠️  Stream test error: {e}")


def test_get_state():
    """Test getting graph state"""
    if not session_id:
        print("⚠️  Skipping state test - no session created")
        return
    
    print("\n📊 Testing Get Graph State")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/chat/state/{session_id}")
    print(f"✅ GET /chat/state/{session_id} - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Current Day: {data.get('current_day')}")
        print(f"   Lesson Plan Exists: {data.get('lesson_plan_exists')}")
        print(f"   Total Messages: {data.get('total_messages')}")
        print(f"   Next Node: {data.get('next_node')}")
        print(f"   Metadata: {json.dumps(data.get('metadata', {}), indent=2)}")


def main():
    """Run all tests"""
    print("🧪 DocuLearn AI - API Endpoint Tests")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    
    try:
        # Test if server is running
        requests.get(f"http://localhost:8001/", timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Server is not running!")
        print("💡 Start the server first:")
        print("   cd ai_service")
        print("   uvicorn app.main:app --reload --port 8001")
        return
    
    # Run all tests
    test_health()
    test_create_session()
    test_get_session()
    test_get_lesson_plan()
    test_chat_invoke()
    test_chat_stream()
    test_get_state()
    
    print("\n" + "=" * 60)
    print("✅ All API tests completed!")
    print(f"📝 Session ID for manual testing: {session_id}")


if __name__ == "__main__":
    main()

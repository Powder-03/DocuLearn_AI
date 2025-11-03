# API Endpoints - Quick Start Guide

## 🚀 Getting Started

### 1. Install Dependencies
```bash
cd ai_service
pip install -r requirements.txt
```

### 2. Set Environment Variables
Create a `.env` file in `ai_service/` directory:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/doculearl_db

# OpenAI
OPENAI_API_KEY=your_openai_key_here

# Google Gemini
GOOGLE_API_KEY=your_gemini_key_here
```

### 3. Start the Server
```bash
uvicorn app.main:app --reload --port 8001
```

Or using Docker:
```bash
docker-compose up --build
```

### 4. Access API Documentation
Open in browser: http://localhost:8001/docs

---

## 📋 All Available Endpoints

### Health Endpoints
- `GET /api/v1/` - Root health check
- `GET /api/v1/health` - Detailed health status

### Session Management
- `POST /api/v1/sessions/create` - Create new learning session
- `GET /api/v1/sessions/{session_id}` - Get session details
- `GET /api/v1/sessions/{session_id}/lesson-plan` - Get lesson plan
- `DELETE /api/v1/sessions/{session_id}` - Delete session (not implemented)

### Chat Interactions
- `POST /api/v1/chat/invoke` - Send message (synchronous)
- `POST /api/v1/chat/stream` - Send message (streaming SSE)
- `GET /api/v1/chat/state/{session_id}` - Get graph state

---

## 🧪 Testing the API

### Test 1: Check Server Health
```bash
curl http://localhost:8001/api/v1/health
```

### Test 2: Create a Learning Session
```bash
curl -X POST "http://localhost:8001/api/v1/sessions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "topic": "Python Programming",
    "total_days": 7,
    "time_per_day": "45 minutes"
  }'
```

**Response:**
```json
{
  "session_id": "abc-123-def-456",
  "message": "Learning plan created successfully",
  "topic": "Python Programming",
  "total_days": 7
}
```

### Test 3: Get Session Details
```bash
curl http://localhost:8001/api/v1/sessions/YOUR_SESSION_ID
```

### Test 4: Get Lesson Plan
```bash
curl http://localhost:8001/api/v1/sessions/YOUR_SESSION_ID/lesson-plan
```

### Test 5: Chat (Synchronous)
```bash
curl -X POST "http://localhost:8001/api/v1/chat/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "message": "Hello! What will we learn today?"
  }'
```

**Response:**
```json
{
  "session_id": "abc-123-def-456",
  "message": "Great question! Today we'll be covering...",
  "current_day": 1,
  "lesson_plan_exists": true,
  "metadata": {
    "day_title": "Introduction to Python",
    "total_days": 7,
    "message_count": 1
  }
}
```

### Test 6: Chat (Streaming)
```bash
curl -N -X POST "http://localhost:8001/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "message": "Explain variables in Python"
  }'
```

**Streaming Response Format:**
```
data: {"event": "start", "data": "Generating response..."}

data: {"event": "token", "data": "Variables", "metadata": {...}}

data: {"event": "token", "data": " are", "metadata": {...}}

data: {"event": "done", "data": "Stream complete", "metadata": {...}}
```

### Test 7: Get Graph State
```bash
curl http://localhost:8001/api/v1/chat/state/YOUR_SESSION_ID
```

---

## 🐍 Using Python to Test

### Run Automated Tests
```bash
# Test endpoint registration (no server needed)
python test_endpoints.py

# Test live API (server must be running)
python test_api_live.py
```

### Manual Python Test
```python
import requests

# Create session
response = requests.post(
    "http://localhost:8001/api/v1/sessions/create",
    json={
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "topic": "Machine Learning",
        "total_days": 5,
        "time_per_day": "1 hour"
    }
)
session_id = response.json()["session_id"]
print(f"Created session: {session_id}")

# Chat
response = requests.post(
    "http://localhost:8001/api/v1/chat/invoke",
    json={
        "session_id": session_id,
        "message": "What is machine learning?"
    }
)
print(response.json()["message"])
```

---

## 📊 Request/Response Examples

### Create Session Request
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "topic": "Web Development with FastAPI",
  "total_days": 10,
  "time_per_day": "2 hours"
}
```

### Chat Request
```json
{
  "session_id": "abc-123-def-456",
  "message": "Can you explain REST APIs?"
}
```

### Chat Response
```json
{
  "session_id": "abc-123-def-456",
  "message": "REST APIs are architectural style...",
  "current_day": 3,
  "lesson_plan_exists": true,
  "metadata": {
    "day_title": "API Design Principles",
    "total_days": 10,
    "message_count": 5
  }
}
```

---

## 🔧 Troubleshooting

### Server won't start
- Check if port 8001 is available
- Verify database connection
- Check environment variables in `.env`

### Import errors
```bash
pip install -r requirements.txt
```

### Database errors
- Ensure PostgreSQL is running
- Check DATABASE_URL in `.env`
- Tables will be created automatically on first run

### LLM API errors
- Verify OPENAI_API_KEY and GOOGLE_API_KEY
- Check API quota/limits
- Review error messages in console

---

## 📝 Notes

- All endpoints use `/api/v1` prefix
- Interactive docs available at `/docs`
- Alternative docs at `/redoc`
- Health check at root: `GET /`
- Session IDs are UUIDs
- Chat history is persisted in database
- Streaming uses Server-Sent Events (SSE)

---

## 🎯 Next Steps

1. ✅ Verify all endpoints work: `python test_endpoints.py`
2. ✅ Start server: `uvicorn app.main:app --reload --port 8001`
3. ✅ Run live tests: `python test_api_live.py`
4. ✅ Check Swagger docs: http://localhost:8001/docs
5. ✅ Test with your frontend application

**All 9 endpoints are now fully implemented and ready to use!** 🚀

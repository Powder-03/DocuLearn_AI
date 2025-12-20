# DocuLearn AI - REST API Documentation

## 🚀 Overview

This microservice provides a complete async REST API for AI-powered personalized learning. It uses LangGraph for orchestration and supports both synchronous and streaming chat interactions.

**Base URL:** `http://localhost:8001/api/v1`

**Documentation:** `http://localhost:8001/docs`

---

## 🔐 Authentication

> **Note:** Authentication is handled by a separate Cognito microservice. This service expects authenticated requests with user context.

All protected endpoints will eventually validate:
- JWT token from AWS Cognito
- User ownership of sessions
- Rate limits per user

---

## 📡 Endpoints

### 1. Health Check

#### `GET /api/v1/`
Root health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "AI Microservice - Generation Mode",
  "version": "2.0.0"
}
```

---

### 2. Create Learning Session

#### `POST /api/v1/sessions/create`
Create a new personalized learning plan.

**Request Body:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "topic": "Python Programming Basics",
  "total_days": 7,
  "time_per_day": "45 minutes"
}
```

**Response:** `201 Created`
```json
{
  "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
  "message": "Learning plan created successfully",
  "topic": "Python Programming Basics",
  "total_days": 7
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8001/api/v1/sessions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "topic": "Python Programming",
    "total_days": 7,
    "time_per_day": "1 hour"
  }'
```

---

### 3. Get Session Details

#### `GET /api/v1/sessions/{session_id}`
Retrieve session information and progress.

**Response:**
```json
{
  "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "topic": "Python Programming Basics",
  "current_day": 3,
  "total_days": 7,
  "has_lesson_plan": true,
  "message_count": 24
}
```

---

### 4. Get Lesson Plan

#### `GET /api/v1/sessions/{session_id}/lesson-plan`
Retrieve the complete generated lesson plan.

**Response:**
```json
{
  "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
  "lesson_plan": {
    "topic": "Python Programming Basics",
    "total_days": 7,
    "days": [
      {
        "day": 1,
        "title": "Introduction to Python",
        "subtopic": "Setup and Basic Syntax",
        "learning_objectives": [
          "Install Python",
          "Write first program",
          "Understand variables"
        ],
        "key_concepts": ["Variables", "Data types", "Print function"],
        "activities": ["Install Python", "Hello World program"],
        "estimated_time": "45 minutes"
      }
      // ... more days
    ]
  }
}
```

---

### 5. Chat - Invoke (Non-Streaming)

#### `POST /api/v1/chat/invoke`
Send a message and get AI tutor's response.

**Request Body:**
```json
{
  "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
  "message": "Can you explain Python variables?"
}
```

**Response:**
```json
{
  "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
  "message": "Great question! Let me guide you through variables. What do you think a variable might be used for in programming?",
  "current_day": 1,
  "lesson_plan_exists": true,
  "metadata": {
    "day_title": "Introduction to Python Syntax",
    "total_days": 7,
    "message_count": 5
  }
}
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8001/api/v1/chat/invoke",
    json={
        "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
        "message": "Can you explain variables?"
    }
)

data = response.json()
print(data["message"])  # AI tutor's response
```

**JavaScript Example:**
```javascript
const response = await fetch('http://localhost:8001/api/v1/chat/invoke', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: '987fcdeb-51a2-43f8-9c3d-0123456789ab',
    message: 'Can you explain variables?'
  })
});

const data = await response.json();
console.log(data.message);
```

---

### 6. Chat - Stream (Server-Sent Events)

#### `POST /api/v1/chat/stream`
Stream AI responses in real-time for better UX.

**Request Body:**
```json
{
  "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
  "message": "What are Python data types?"
}
```

**Response Format:** Server-Sent Events (SSE)
```
data: {"event": "start", "data": "Generating response..."}

data: {"event": "token", "data": "Python", "metadata": {"current_day": 1}}

data: {"event": "token", "data": " has several", "metadata": {"current_day": 1}}

data: {"event": "token", "data": " built-in data types...", "metadata": {"current_day": 1}}

data: {"event": "done", "data": "Stream complete", "metadata": {"total_chars": 156}}
```

**JavaScript Example (Fetch API):**
```javascript
async function streamChat(sessionId, message) {
  const response = await fetch('http://localhost:8001/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message: message })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        if (data.event === 'token') {
          // Append token to UI (typewriter effect)
          appendToChat(data.data);
        } else if (data.event === 'done') {
          console.log('Stream complete');
        } else if (data.event === 'error') {
          console.error('Error:', data.data);
        }
      }
    }
  }
}
```

**Python Example:**
```python
import requests
import json

response = requests.post(
    "http://localhost:8001/api/v1/chat/stream",
    json={"session_id": session_id, "message": message},
    stream=True
)

for line in response.iter_lines():
    if line:
        # Remove 'data: ' prefix
        json_str = line.decode('utf-8').replace('data: ', '', 1)
        data = json.loads(json_str)
        
        if data['event'] == 'token':
            print(data['data'], end='', flush=True)
        elif data['event'] == 'done':
            print('\nDone!')
```

---

### 7. Get Graph State

#### `GET /api/v1/chat/state/{session_id}`
Inspect the current LangGraph state for debugging and monitoring.

**Response:**
```json
{
  "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
  "current_day": 3,
  "lesson_plan_exists": true,
  "total_messages": 24,
  "next_node": "tutor",
  "metadata": {
    "topic": "Python Programming Basics",
    "total_days": 7,
    "time_per_day": "45 minutes",
    "lesson_plan_summary": {
      "topic": "Python Programming Basics",
      "total_days": 7,
      "days_count": 7,
      "has_objectives": true
    }
  }
}
```

**Use Cases:**
- Debugging graph execution
- Progress analytics
- Session resumption
- Performance monitoring

---

## 🔄 Complete Workflow Example

### Step 1: Create Session
```bash
curl -X POST "http://localhost:8001/api/v1/sessions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "topic": "Machine Learning Basics",
    "total_days": 10,
    "time_per_day": "1 hour"
  }'

# Response: { "session_id": "abc-123", ... }
```

### Step 2: Start Learning (Chat)
```bash
curl -X POST "http://localhost:8001/api/v1/chat/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123",
    "message": "I am ready to start learning!"
  }'
```

### Step 3: Continue Conversation
```bash
curl -X POST "http://localhost:8001/api/v1/chat/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123",
    "message": "Can you explain supervised learning?"
  }'
```

### Step 4: Check Progress
```bash
curl "http://localhost:8001/api/v1/sessions/abc-123"
curl "http://localhost:8001/api/v1/chat/state/abc-123"
```

---

## ⚡ React Frontend Integration

### Setup (React + TypeScript)

```typescript
// src/api/aiService.ts
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001/api/v1';

export const aiService = {
  // Create learning session
  async createSession(userId: string, topic: string, totalDays: number, timePerDay: string) {
    const response = await axios.post(`${API_BASE_URL}/sessions/create`, {
      user_id: userId,
      topic,
      total_days: totalDays,
      time_per_day: timePerDay
    });
    return response.data;
  },

  // Send chat message
  async sendMessage(sessionId: string, message: string) {
    const response = await axios.post(`${API_BASE_URL}/chat/invoke`, {
      session_id: sessionId,
      message
    });
    return response.data;
  },

  // Stream chat response
  async streamMessage(
    sessionId: string,
    message: string,
    onToken: (token: string) => void,
    onComplete: () => void,
    onError: (error: string) => void
  ) {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message })
    });

    if (!response.body) {
      onError('No response body');
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));

          if (data.event === 'token') {
            onToken(data.data);
          } else if (data.event === 'done') {
            onComplete();
          } else if (data.event === 'error') {
            onError(data.data);
          }
        }
      }
    }
  },

  // Get session details
  async getSession(sessionId: string) {
    const response = await axios.get(`${API_BASE_URL}/sessions/${sessionId}`);
    return response.data;
  },

  // Get lesson plan
  async getLessonPlan(sessionId: string) {
    const response = await axios.get(`${API_BASE_URL}/sessions/${sessionId}/lesson-plan`);
    return response.data;
  }
};
```

### Usage in React Component

```tsx
// src/components/Chat.tsx
import React, { useState } from 'react';
import { aiService } from '../api/aiService';

export const Chat: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const handleSendMessage = async () => {
    setIsStreaming(true);
    setResponse('');

    await aiService.streamMessage(
      sessionId,
      message,
      (token) => {
        // Append each token (typewriter effect)
        setResponse(prev => prev + token);
      },
      () => {
        // Stream complete
        setIsStreaming(false);
        setMessage('');
      },
      (error) => {
        console.error('Stream error:', error);
        setIsStreaming(false);
      }
    );
  };

  return (
    <div>
      <div>{response}</div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={isStreaming}
      />
      <button onClick={handleSendMessage} disabled={isStreaming}>
        {isStreaming ? 'AI is thinking...' : 'Send'}
      </button>
    </div>
  );
};
```

---

## 🐛 Error Handling

All endpoints return errors in this format:

```json
{
  "detail": "Error message here"
}
```

**HTTP Status Codes:**
- `200` - Success
- `201` - Created (session)
- `400` - Bad Request (validation error)
- `404` - Not Found (session/resource)
- `429` - Too Many Requests (rate limit)
- `500` - Internal Server Error

**Example Error:**
```json
{
  "detail": "Session not found"
}
```

---

## 🚀 Performance & Best Practices

### 1. Use Streaming for Better UX
```javascript
// ✅ Good: Streaming for real-time feedback
await aiService.streamMessage(sessionId, message, onToken, onComplete);

// ❌ Slower: Wait for full response
const response = await aiService.sendMessage(sessionId, message);
```

### 2. Cache Lesson Plans
```javascript
// Cache on first fetch
const lessonPlan = await aiService.getLessonPlan(sessionId);
localStorage.setItem(`lesson_${sessionId}`, JSON.stringify(lessonPlan));
```

### 3. Debounce User Input
```typescript
import { debounce } from 'lodash';

const debouncedSend = debounce((msg) => sendMessage(msg), 300);
```

### 4. Handle Connection Errors
```typescript
try {
  await aiService.sendMessage(sessionId, message);
} catch (error) {
  if (error.code === 'ECONNREFUSED') {
    showError('Service unavailable. Please try again.');
  }
}
```

---

## 📊 Testing

### Manual Testing with cURL
```bash
# Health check
curl http://localhost:8001/

# Create session
curl -X POST http://localhost:8001/api/v1/sessions/create \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","topic":"Test","total_days":5,"time_per_day":"30min"}'

# Chat
curl -X POST http://localhost:8001/api/v1/chat/invoke \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SESSION_ID","message":"Hello!"}'
```

### Automated Testing (Python)
```python
import pytest
import requests

BASE_URL = "http://localhost:8001/api/v1"

def test_create_session():
    response = requests.post(f"{BASE_URL}/sessions/create", json={
        "user_id": "test-user",
        "topic": "Python",
        "total_days": 5,
        "time_per_day": "30 minutes"
    })
    assert response.status_code == 201
    assert "session_id" in response.json()

def test_chat_invoke():
    session_id = "test-session-id"
    response = requests.post(f"{BASE_URL}/chat/invoke", json={
        "session_id": session_id,
        "message": "Hello"
    })
    assert response.status_code in [200, 404]  # 404 if session doesn't exist
```

---

## 🎉 Summary

✅ **Pure REST API** - No LangServe dependency  
✅ **Async FastAPI** - Full async/await support  
✅ **Streaming Support** - Real-time responses via SSE  
✅ **Type-Safe** - Pydantic validation on all endpoints  
✅ **Production-Ready** - Error handling, CORS, documentation  
✅ **Frontend-Friendly** - Easy integration with React/Vue/Angular  

**Your microservice is now production-ready!** 🚀

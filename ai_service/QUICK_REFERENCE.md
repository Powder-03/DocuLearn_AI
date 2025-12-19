# Quick Reference Guide

## 🚀 Common Tasks

### Adding a New Endpoint

1. **Create/Update Schema** (`app/schemas/`)
```python
# app/schemas/quiz.py
from pydantic import BaseModel

class QuizRequest(BaseModel):
    session_id: str
    questions: int = 5

class QuizResponse(BaseModel):
    quiz_id: str
    questions: list[str]
```

2. **Create Route Handler** (`app/api/routes/`)
```python
# app/api/routes/quiz.py
from fastapi import APIRouter, HTTPException
from app.schemas.quiz import QuizRequest, QuizResponse

router = APIRouter(prefix="/quiz", tags=["Quiz"])

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    # Your logic here
    pass
```

3. **Register Router** (`app/api/router.py`)
```python
from app.api.routes import quiz

api_router.include_router(quiz.router)
```

---

### Adding Business Logic

**Create Service** (`app/services/`)
```python
# app/services/quiz_generator.py
def generate_quiz(session_id: str, num_questions: int):
    """Business logic for quiz generation."""
    # Implementation
    pass
```

**Use in Route**
```python
from app.services.quiz_generator import generate_quiz

@router.post("/generate")
async def generate_quiz_endpoint(request: QuizRequest):
    quiz = generate_quiz(request.session_id, request.questions)
    return quiz
```

---

### Adding Database Model

1. **Define Model** (`app/db/models.py`)
```python
class Quiz(Base):
    __tablename__ = "quizzes"
    
    quiz_id = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("learning_sessions.session_id"))
    questions = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
```

2. **Create Migration** (if using Alembic)
```bash
alembic revision --autogenerate -m "add quiz table"
alembic upgrade head
```

---

### Adding Dependency

**Define in deps.py** (`app/api/deps.py`)
```python
async def get_current_user(token: str = Header(...)):
    """Validate user token."""
    user = validate_token(token)
    if not user:
        raise HTTPException(status_code=401)
    return user
```

**Use in Route**
```python
from fastapi import Depends
from app.api.deps import get_current_user

@router.post("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user": user}
```

---

## 📂 File Locations Cheat Sheet

| Task | Location | Example |
|------|----------|---------|
| **Add API endpoint** | `app/api/routes/` | `sessions.py`, `health.py` |
| **Add request/response model** | `app/schemas/` | `session.py` |
| **Add business logic** | `app/services/` | `memory.py` |
| **Add database model** | `app/db/models.py` | `LearningSession` |
| **Add configuration** | `app/core/config.py` | Settings |
| **Add dependency** | `app/api/deps.py` | `get_db()` |
| **Register router** | `app/api/router.py` | `include_router()` |
| **Add LangGraph node** | `app/graphs/` | `generation_graph.py` |

---

## 🧪 Testing Patterns

### Unit Test (Service)
```python
# tests/services/test_memory.py
def test_create_session(mock_db):
    session_id = create_session(
        user_id="test-uuid",
        topic="Test Topic",
        total_days=5,
        time_per_day="30 min"
    )
    assert session_id is not None
```

### Integration Test (API)
```python
# tests/api/test_sessions.py
def test_create_plan_endpoint(client):
    response = client.post("/sessions/create", json={
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "topic": "Test",
        "total_days": 5,
        "time_per_day": "30 minutes"
    })
    assert response.status_code == 201
    assert "session_id" in response.json()
```

---

## 🎯 API Endpoint Patterns

### Standard CRUD
```python
router = APIRouter(prefix="/resource", tags=["Resource"])

@router.post("/", status_code=201)           # Create
async def create_resource(): pass

@router.get("/{id}")                         # Read
async def get_resource(id: str): pass

@router.get("/")                             # List
async def list_resources(): pass

@router.put("/{id}")                         # Update
async def update_resource(id: str): pass

@router.delete("/{id}", status_code=204)     # Delete
async def delete_resource(id: str): pass
```

---

## 🔧 Common Imports

### Route Handler
```python
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.your_schema import RequestModel, ResponseModel
from app.services.your_service import your_function
```

### Service
```python
from typing import Dict, Any, Optional
from app.db.session import SessionLocal
from app.db.models import YourModel
```

### Schema
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
```

---

## 🐛 Common Issues & Solutions

### Import Error: "Module not found"
```python
# ❌ Wrong
from schemas import CreatePlanRequest

# ✅ Correct
from app.schemas import CreatePlanRequest
```

### Router Not Registered
```python
# app/api/router.py
from app.api.routes import your_new_route

api_router.include_router(your_new_route.router)  # Don't forget!
```

### Database Session Not Closing
```python
# ✅ Use dependency injection
from app.api.deps import get_db

@router.get("/")
async def endpoint(db = Depends(get_db)):
    # db automatically closed after request
    pass
```

---

## 📊 Project Structure at a Glance

```
app/
├── main.py                      # 🚀 Start here
├── core/
│   ├── config.py               # ⚙️ Settings
│   └── llm_factory.py          # 🤖 LLM provider
├── api/
│   ├── deps.py                 # 🔧 Dependencies
│   ├── router.py               # 📍 Route aggregator
│   └── routes/
│       ├── health.py           # ❤️ Health checks
│       ├── sessions.py         # 📚 Sessions
│       └── chat.py             # 🧠 Chat
├── schemas/
│   └── session.py              # 📋 Pydantic models
├── db/
│   ├── models.py               # 🗄️ DB models
│   └── session.py              # 🔌 DB connection
├── graphs/
│   ├── state.py                # 📊 Graph state
│   └── generation_graph.py     # 🧠 LangGraph
└── services/
    └── memory.py               # 💾 Persistence
```

---

## 🎨 Code Style Guidelines

### Naming Conventions
```python
# Files: snake_case
user_service.py

# Classes: PascalCase
class UserService:

# Functions: snake_case
def get_user():

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3

# Private: _prefix
def _internal_helper():
```

### Docstrings
```python
async def create_session(user_id: str) -> str:
    """
    Create a new learning session.
    
    Args:
        user_id: UUID of the user
        
    Returns:
        session_id: UUID of the created session
        
    Raises:
        ValueError: If user_id is invalid
    """
    pass
```

---

## 🚀 Deployment Checklist

- [ ] Update `.env` with production values
- [ ] Set `allow_origins` in CORS middleware
- [ ] Enable HTTPS
- [ ] Add authentication middleware
- [ ] Set up logging
- [ ] Configure rate limiting
- [ ] Add monitoring/metrics
- [ ] Set up health check monitoring
- [ ] Configure database connection pooling
- [ ] Add error tracking (Sentry, etc.)

---

## 📚 Useful Commands

```bash
# Development
uvicorn app.main:app --reload --port 8001

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4

# Docker
docker-compose up --build
docker-compose down -v

# Testing
pytest tests/
pytest tests/ -v --cov=app

# Linting
ruff check app/
black app/
mypy app/
```

---

**Keep this guide handy for quick reference!** 📖

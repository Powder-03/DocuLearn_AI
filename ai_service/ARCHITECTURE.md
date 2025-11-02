# API Architecture Documentation

## 📁 Refactored Project Structure

```
ai_service/
├── app/
│   ├── api/                    # API Layer
│   │   ├── __init__.py
│   │   ├── deps.py            # Shared dependencies (DB sessions, auth)
│   │   ├── router.py          # Main API router aggregator
│   │   └── routes/            # Route modules
│   │       ├── __init__.py
│   │       ├── health.py      # Health check endpoints
│   │       ├── sessions.py    # Session management endpoints
│   │       └── langserve.py   # LangServe integration
│   │
│   ├── core/                   # Core Configuration
│   │   ├── __init__.py
│   │   ├── config.py          # Settings & environment
│   │   └── llm_factory.py     # LLM provider factory
│   │
│   ├── db/                     # Database Layer
│   │   ├── __init__.py
│   │   ├── models.py          # SQLAlchemy models
│   │   └── session.py         # Database session management
│   │
│   ├── graphs/                 # LangGraph Workflows
│   │   ├── __init__.py
│   │   ├── state.py           # Graph state definitions
│   │   └── generation_graph.py # Main learning graph
│   │
│   ├── schemas/                # Pydantic Models
│   │   ├── __init__.py
│   │   └── session.py         # Session request/response schemas
│   │
│   ├── services/               # Business Logic
│   │   ├── __init__.py
│   │   └── memory.py          # Session persistence service
│   │
│   ├── __init__.py
│   └── main.py                # FastAPI app entry point (CLEAN!)
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

## 🎯 Architecture Principles

### 1. **Separation of Concerns**
   - **API Layer** (`app/api/`): HTTP concerns, routing, validation
   - **Business Logic** (`app/services/`): Core functionality
   - **Data Layer** (`app/db/`): Database models and access
   - **Schemas** (`app/schemas/`): Data validation and serialization
   - **Configuration** (`app/core/`): Settings and factories

### 2. **Dependency Injection**
   - Shared dependencies in `app/api/deps.py`
   - Easy to mock for testing
   - Clear dependency flow

### 3. **Modular Routing**
   - Each domain gets its own router module
   - Easy to add new features
   - Clear API organization

### 4. **Type Safety**
   - Pydantic models for all requests/responses
   - Full IDE autocomplete support
   - Runtime validation

## 📋 API Endpoints

### **Health & Status**
- `GET /` - Root health check
- `GET /health` - Detailed health status

### **Session Management**
- `POST /sessions/create` - Create new learning plan
- `GET /sessions/{session_id}` - Get session details
- `GET /sessions/{session_id}/lesson-plan` - Get lesson plan
- `DELETE /sessions/{session_id}` - Delete session (soft delete)

### **LangServe (AI Chat)**
- `POST /learn/generation/invoke` - Synchronous chat
- `POST /learn/generation/stream` - Streaming chat
- `GET /learn/generation/playground` - Interactive UI

## 🔄 Request Flow

```
Client Request
    ↓
FastAPI Middleware (CORS, etc.)
    ↓
API Router (app/api/router.py)
    ↓
Route Handler (app/api/routes/*.py)
    ↓
Schema Validation (app/schemas/*.py)
    ↓
Business Logic (app/services/*.py)
    ↓
Database/Graph (app/db/* or app/graphs/*)
    ↓
Response (validated by schema)
    ↓
Client
```

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/test_services.py
def test_create_session(mock_db):
    """Test session creation logic."""
    pass

# tests/test_schemas.py
def test_create_plan_request_validation():
    """Test request validation."""
    pass
```

### Integration Tests
```python
# tests/test_api.py
def test_create_plan_endpoint(client):
    """Test full endpoint flow."""
    response = client.post("/sessions/create", json={...})
    assert response.status_code == 201
```

## 🚀 Adding New Features

### Example: Add Progress Tracking

1. **Create Schema** (`app/schemas/progress.py`):
```python
class ProgressResponse(BaseModel):
    session_id: str
    completed_days: int
    quiz_scores: List[float]
```

2. **Add Route** (`app/api/routes/progress.py`):
```python
router = APIRouter(prefix="/progress", tags=["Progress"])

@router.get("/{session_id}", response_model=ProgressResponse)
async def get_progress(session_id: str):
    # Implementation
    pass
```

3. **Register Router** (`app/api/router.py`):
```python
from app.api.routes import progress

api_router.include_router(progress.router)
```

## 🔐 Future Enhancements

- [ ] Add authentication middleware
- [ ] Implement rate limiting
- [ ] Add request/response logging
- [ ] Create OpenAPI spec generator
- [ ] Add GraphQL support
- [ ] Implement caching layer
- [ ] Add monitoring/metrics endpoints

## 📖 Code Examples

### Creating a Session
```bash
curl -X POST "http://localhost:8001/sessions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "topic": "Python Programming",
    "total_days": 7,
    "time_per_day": "45 minutes"
  }'
```

### Getting Session Details
```bash
curl "http://localhost:8001/sessions/{session_id}"
```

### Interactive Playground
Visit: `http://localhost:8001/learn/generation/playground`

## 🎨 Benefits of This Structure

| Aspect | Before | After |
|--------|--------|-------|
| **Lines in main.py** | 120+ | ~50 |
| **Testability** | Hard to mock | Easy to test |
| **Maintainability** | Monolithic | Modular |
| **Onboarding** | Confusing | Clear structure |
| **Scalability** | Limited | Easy to extend |
| **Type Safety** | Partial | Full |
| **Documentation** | Minimal | Self-documenting |

## 📝 Migration Notes

### Breaking Changes
- `POST /create_plan` → `POST /sessions/create`
- `GET /session/{id}` → `GET /sessions/{id}`
- Response format includes additional metadata

### Backward Compatibility
If needed, add aliases in `main.py`:
```python
# Legacy endpoint support
@app.post("/create_plan")
async def legacy_create_plan(request: CreatePlanRequest):
    return await create_learning_plan(request)
```

---

**This architecture is now production-ready and follows FastAPI best practices!** 🚀

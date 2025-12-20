# AI Microservice - Generation Mode

A standalone AI microservice for personalized learning plan generation and tutoring, powered by LangGraph and LangServe.

## Features

- 🧠 **AI Pipeline**: Plan generation and interactive tutoring with Google Gemini.
- 💾 **PostgreSQL Persistence**: All session state, chat history, and plans stored in database
- 🔄 **Stateful LangGraph**: Two-node graph with conditional routing
- 🚀 **LangServe Integration**: RESTful API with streaming support
- 🐳 **Docker-Ready**: Complete containerization with Docker Compose

## Architecture

### Graph Flow

```
Entry Point (conditional)
    ↓
    ├─→ plan_generator (if no lesson_plan) → tutor → END
    └─→ tutor (if lesson_plan exists) → END
```

### Technology Stack

- **API Framework**: FastAPI + LangServe
- **AI Orchestration**: LangGraph + LangChain
- **LLMs**: Google Gemini
- **Database**: PostgreSQL with SQLAlchemy
- **Containerization**: Docker + Docker Compose

## Setup

### Prerequisites

- Docker and Docker Compose
- API key for Google Gemini

### Installation

1. **Clone and navigate to the service:**
   ```bash
   cd ai_service
   ```

2. **Configure environment variables:**
   Edit `.env` file with your API key:
   ```env
   GOOGLE_API_KEY=your_actual_google_api_key
   ```

3. **Build and start services:**
   ```bash
   docker-compose up --build
   ```

4. **Verify services:**
   - API: http://localhost:8001
   - API Docs: http://localhost:8001/docs
   - PostgreSQL: localhost:5432

## Usage

### 1. Create a Learning Plan

```bash
curl -X POST "http://localhost:8001/api/v1/sessions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "topic": "Introduction to Machine Learning",
    "total_days": 7,
    "time_per_day": "30 minutes"
  }'
```

Response:
```json
{
  "session_id": "987fcdeb-51a2-43f8-9c3d-0123456789ab",
  "message": "Learning plan created successfully for topic: Introduction to Machine Learning"
}
```

### 2. Chat with the Tutor

Use the chat endpoint at `/api/v1/chat/invoke` with the returned `session_id`.

### 3. Check Session Status

```bash
curl "http://localhost:8001/api/v1/sessions/987fcdeb-51a2-43f8-9c3d-0123456789ab"
```

## Project Structure

```
ai_service/
├── app/
│   ├── core/
│   │   ├── config.py          # Settings & environment variables
│   │   └── llm_factory.py     # LLM provider factory
│   ├── db/
│   │   ├── models.py          # SQLAlchemy models
│   │   └── session.py         # Database session management
│   ├── graphs/
│   │   ├── state.py           # Graph state definition
│   │   └── generation_graph.py # LangGraph workflow
│   ├── services/
│   │   └── memory.py          # Database I/O service
│   └── main.py                # FastAPI application entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

## API Endpoints

### Core Endpoints

- `GET /` - Health check
- `POST /api/v1/sessions/create` - Initialize a new learning session
- `GET /api/v1/sessions/{session_id}` - Get session status
- `POST /api/v1/chat/invoke` - Synchronous invocation
- `POST /api/v1/chat/stream` - Streaming responses
- `GET /api/v1/chat/state/{session_id}` - Get chat state

## Database Schema

### `learning_sessions` Table

| Column | Type | Description |
|--------|------|-------------|
| session_id | UUID | Primary key |
| user_id | UUID | User identifier (from auth service) |
| mode | String | Learning mode (default: 'generation') |
| topic | String | Learning topic |
| lesson_plan | JSONB | Generated lesson plan |
| chat_history | JSONB | Message history |
| memory_summary | Text | Conversation summary |
| current_day | Integer | Current day in the plan |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| total_days | INTEGER | Total number of days for the learning plan. |
| time_per_day | VARCHAR | Time allocated per day for learning. |

## Deployment

This service is designed to be deployed on **Google Cloud Run**.

For detailed deployment instructions, please refer to [GCP_DEPLOYMENT.md](GCP_DEPLOYMENT.md).

## Development

### Running Locally (without Docker)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start PostgreSQL separately

3. Update `.env` with local database URL:
   ```env
   DATABASE_URL=postgresql+psycopg://admin:supersecret@localhost:5432/learning_saas_db
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

### Testing

Access the interactive API docs at http://localhost:8001/docs to test all endpoints.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| DATABASE_URL | PostgreSQL connection string | Yes |
| GOOGLE_API_KEY | Google Gemini API key | Yes |
| POSTGRES_USER | Database username | Yes (Docker) |
| POSTGRES_PASSWORD | Database password | Yes (Docker) |
| POSTGRES_DB | Database name | Yes (Docker) |

## Notes

- **No Authentication**: This service does NOT handle user authentication. It assumes `user_id` is provided by an upstream service.
- **Session Management**: All state is persisted to PostgreSQL. The graph nodes call `services.memory` for all I/O operations.
- **LLM Switching**: Use `llm_factory.get_llm()` to switch between models for different tasks.
- **Persistence**: No LangGraph checkpointer is used; all persistence is manual via database calls.

## Future Enhancements

- [ ] Implement periodic memory summarization
- [ ] Add support for advancing to next day
- [ ] Implement quiz/assessment features
- [ ] Add support for additional learning modes
- [ ] Add metrics and monitoring
- [ ] Implement retry logic for LLM calls

## License

MIT

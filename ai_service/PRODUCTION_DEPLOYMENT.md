# Production Deployment Guide

## ✅ Changes Made for Production

### Removed:
- ❌ Test endpoints (`/api/test/*`)
- ❌ Test scripts (`test_*.py`)
- ❌ Default `user_id = "test-user"` from all endpoints

### Required:
- ✅ `user_id` is now **required** in all session creation requests
- ✅ `user_id` must come from your Cognito authentication service
- ✅ All endpoints now expect authenticated user IDs

---

## 🔐 AWS Cognito Integration

### Expected Flow:

```
User Login → AWS Cognito → JWT Token
                              ↓
                    Extract user_id (sub claim)
                              ↓
                    Frontend includes in API calls
                              ↓
                    AI Service validates & processes
```

### Implementation Steps:

#### 1. **Frontend: Get User ID from Cognito**

```javascript
import { Auth } from 'aws-amplify';

// After user login
const user = await Auth.currentAuthenticatedUser();
const userId = user.attributes.sub; // This is the Cognito user ID (UUID)

// Use this userId in API calls
const response = await fetch('https://your-api.com/api/v1/sessions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${user.signInUserSession.idToken.jwtToken}`
  },
  body: JSON.stringify({
    user_id: userId,  // From Cognito
    topic: 'Python Programming',
    total_days: 7,
    time_per_day: '30 minutes'
  })
});
```

#### 2. **API Gateway: Add JWT Validation** (Optional but Recommended)

```yaml
# If using API Gateway, add Cognito authorizer
authorizers:
  CognitoAuthorizer:
    type: COGNITO_USER_POOLS
    userPoolArn: arn:aws:cognito-idp:region:account-id:userpool/pool-id
```

#### 3. **Alternative: FastAPI Middleware for JWT Validation**

```python
# Add to app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import jwt
from jwt import PyJWKClient

security = HTTPBearer()
COGNITO_REGION = "us-east-1"
COGNITO_USER_POOL_ID = "your-pool-id"
COGNITO_APP_CLIENT_ID = "your-client-id"

jwks_url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
jwks_client = PyJWKClient(jwks_url)

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    try:
        token = credentials.credentials
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID
        )
        
        return payload["sub"]  # Returns user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Then use in routes:
# async def create_session(
#     request: SessionCreateRequest,
#     user_id: str = Depends(get_current_user)
# ):
```

---

## 🚀 Deployment Steps

### 1. **Environment Variables**

Create `.env` file or set in your deployment platform:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
MONGODB_URI=mongodb://user:password@host:27017/dbname

# AI Service
GEMINI_API_KEY=your-gemini-api-key

# Cognito (if using FastAPI middleware)
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_APP_CLIENT_ID=your-app-client-id

# Server
PORT=8001
ENVIRONMENT=production
```

### 2. **Build Docker Image**

```bash
docker build -t ai-service:production .
```

### 3. **Deploy Options**

#### Option A: AWS ECS/Fargate
```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker tag ai-service:production ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ai-service:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ai-service:latest
```

#### Option B: Docker Compose (VPS/EC2)
```bash
docker compose -f docker-compose.prod.yml up -d
```

#### Option C: Kubernetes
```bash
kubectl apply -f k8s/deployment.yaml
```

### 4. **Database Migrations**

```bash
# Run migrations before starting the service
docker exec ai-service alembic upgrade head
```

---

## 📋 API Usage with Cognito

### Example: Creating a Session

```bash
curl -X POST "https://your-api.com/api/v1/sessions" \
  -H "Authorization: Bearer ${COGNITO_JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "cognito-user-uuid-from-token",
    "topic": "Machine Learning Fundamentals",
    "total_days": 7,
    "time_per_day": "1 hour"
  }'
```

### Example: Chat

```bash
curl -X POST "https://your-api.com/api/v1/chat/invoke" \
  -H "Authorization: Bearer ${COGNITO_JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-uuid",
    "message": "Explain variables in Python"
  }'
```

---

## 🔍 Health Check

```bash
curl https://your-api.com/api/v1/health
```

Expected Response:
```json
{
  "status": "healthy",
  "service": "AI Microservice - Generation Mode",
  "version": "1.0.0"
}
```

---

## ⚠️ Security Checklist

- [ ] All test endpoints removed
- [ ] JWT validation implemented (API Gateway or FastAPI)
- [ ] Environment variables secured
- [ ] CORS configured for your frontend domain only
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Database credentials rotated
- [ ] Gemini API key secured
- [ ] Logs sanitized (no sensitive data)

---

## 📊 Monitoring

Set up monitoring for:
- API response times
- Error rates
- Gemini API quota usage
- Database connection pool
- Memory/CPU usage

---

## 🆘 Troubleshooting

### Issue: "User ID is required"
- **Cause**: Frontend not sending `user_id`
- **Fix**: Ensure Cognito `sub` is extracted and sent in request body

### Issue: "Invalid authentication credentials"
- **Cause**: JWT token expired or invalid
- **Fix**: Refresh Cognito token on frontend

### Issue: "RESOURCE_EXHAUSTED" (Gemini API)
- **Cause**: API quota exceeded
- **Fix**: Upgrade Gemini API plan or implement rate limiting

---

## 📞 Support

For issues or questions, check:
- API Documentation: `https://your-api.com/docs`
- Architecture: See `ARCHITECTURE.md`
- Quick Reference: See `QUICK_REFERENCE.md`

---

**Your AI service is now production-ready! 🚀**

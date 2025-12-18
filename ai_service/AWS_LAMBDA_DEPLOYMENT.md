# AWS Lambda Deployment Guide

## Prerequisites

1. **AWS Account** (Free Tier)
2. **AWS CLI** installed and configured
3. **Docker** (for packaging dependencies)
4. **Node.js** (for Serverless Framework)

## Quick Setup

### 1. Install AWS CLI

```bash
# Windows (PowerShell)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Verify installation
aws --version
```

### 2. Configure AWS Credentials

```bash
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region: us-east-1
# Default output format: json
```

### 3. Install Serverless Framework

```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements
```

### 4. Install Python Dependencies

```bash
cd ai_service
pip install -r requirements-lambda.txt
```

## Deployment Options

### Option A: Serverless Framework (Recommended)

```bash
# Install Serverless plugins
npm install

# Deploy to AWS Lambda
serverless deploy

# Output will show your API endpoint:
# endpoint: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com
```

### Option B: AWS SAM (Serverless Application Model)

Create `template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Timeout: 30
    MemorySize: 1024
    Runtime: python3.11
    Environment:
      Variables:
        DATABASE_URL: {{resolve:ssm:/doculearn/database_url}}
        MONGODB_URL: {{resolve:ssm:/doculearn/mongodb_url}}
        GROQ_API_KEY: {{resolve:ssm:/doculearn/groq_api_key}}

Resources:
  DocuLearnApi:
    Type: AWS::Serverless::Function
    Properties:
      Handler: lambda_handler.handler
      CodeUri: .
      Events:
        ApiEvent:
          Type: HttpApi
          Properties:
            Path: /{proxy+}
            Method: ANY
```

Deploy:

```bash
# Store secrets in AWS Systems Manager
aws ssm put-parameter --name /doculearn/database_url --value "postgresql://..." --type SecureString
aws ssm put-parameter --name /doculearn/mongodb_url --value "mongodb+srv://..." --type SecureString
aws ssm put-parameter --name /doculearn/groq_api_key --value "gsk_..." --type SecureString

# Build and deploy
sam build
sam deploy --guided
```

### Option C: Manual Lambda Deployment

```bash
# Create deployment package
cd ai_service
pip install -r requirements-lambda.txt -t package/
cp -r app package/
cp lambda_handler.py package/
cd package
zip -r ../deployment.zip .

# Create Lambda function
aws lambda create-function \
  --function-name doculearn-ai \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_handler.handler \
  --zip-file fileb://../deployment.zip \
  --timeout 30 \
  --memory-size 1024 \
  --environment Variables="{DATABASE_URL=postgresql://...,MONGODB_URL=mongodb+srv://...,GROQ_API_KEY=gsk_...}"

# Create API Gateway
aws apigatewayv2 create-api \
  --name doculearn-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:doculearn-ai
```

### Option D: AWS Lambda Container (Docker)

Create `Dockerfile.lambda`:

```dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements
COPY requirements-lambda.txt ${LAMBDA_TASK_ROOT}/

# Install dependencies
RUN pip install -r requirements-lambda.txt

# Copy application code
COPY app ${LAMBDA_TASK_ROOT}/app
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD ["lambda_handler.handler"]
```

Deploy:

```bash
# Build container
docker build -f Dockerfile.lambda -t doculearn-lambda .

# Tag for ECR
docker tag doculearn-lambda:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/doculearn-lambda:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/doculearn-lambda:latest

# Create Lambda from container
aws lambda create-function \
  --function-name doculearn-ai \
  --package-type Image \
  --code ImageUri=YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/doculearn-lambda:latest \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role
```

## Environment Variables Setup

```bash
# Using AWS CLI
aws lambda update-function-configuration \
  --function-name doculearn-ai \
  --environment Variables="{
    DATABASE_URL=<YOUR_NEON_DATABASE_URL>,
    MONGODB_URL=<YOUR_MONGODB_ATLAS_URL>,
    GROQ_API_KEY=<YOUR_GROQ_API_KEY>,
    MONGO_DB=learning_saas_chats
  }"
```

## Testing Your Lambda

```bash
# Test endpoint
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/

# Create session
curl -X POST "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/api/v1/sessions/create" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "topic": "Python Programming",
    "total_days": 7,
    "time_per_day": "30 minutes"
  }'

# Health check
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/api/v1/health
```

## AWS Lambda Free Tier Limits

| Resource | Free Tier | Your Usage (Estimate) |
|----------|-----------|------------------------|
| **Requests** | 1M/month | ~100K/month (plenty) |
| **Compute** | 400K GB-seconds | ~50K GB-seconds |
| **Storage** | 512 MB | ~200 MB (deployment) |
| **Cost** | $0 | $0 (within free tier) |

## Monitoring & Logs

```bash
# View logs
aws logs tail /aws/lambda/doculearn-ai --follow

# View metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=doculearn-ai \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-12-31T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## Optimization Tips

1. **Cold Start Optimization**
   - Use provisioned concurrency (may cost extra)
   - Keep deployment package small (<50MB)
   - Use Lambda layers for dependencies

2. **Database Connection Pooling**
   - Already configured in `db/session.py`
   - MongoDB connection reuse enabled

3. **API Gateway Caching**
   - Enable caching for frequently accessed endpoints
   - Set TTL to 300 seconds

4. **Cost Management**
   - Set CloudWatch alarms for budget
   - Use AWS Cost Explorer
   - Monitor Lambda execution time

## Troubleshooting

### Cold Start Issues
```bash
# Increase memory (faster CPU)
aws lambda update-function-configuration \
  --function-name doculearn-ai \
  --memory-size 2048
```

### Database Connection Timeouts
- Increase Lambda timeout to 60 seconds
- Check security groups/network settings
- Verify Neon and Atlas allow AWS IPs

### Package Size Too Large
```bash
# Use Lambda layers
serverless deploy --layer
```

## Custom Domain Setup

```bash
# Create custom domain
aws apigatewayv2 create-domain-name \
  --domain-name api.doculearn.com \
  --domain-name-configurations CertificateArn=arn:aws:acm:...

# Map to your API
aws apigatewayv2 create-api-mapping \
  --domain-name api.doculearn.com \
  --api-id YOUR_API_ID \
  --stage $default
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Database connections tested
- [ ] API Gateway endpoints working
- [ ] CloudWatch logs enabled
- [ ] Error handling tested
- [ ] CORS configured for frontend
- [ ] Custom domain setup (optional)
- [ ] Monitoring alerts configured
- [ ] Backup strategy in place

## Next Steps

1. Deploy to AWS Lambda
2. Test all endpoints
3. Configure CloudWatch alarms
4. Set up CI/CD (GitHub Actions)
5. Monitor usage and optimize

Your DocuLearn AI service is ready for AWS Lambda Free Tier deployment! 🚀

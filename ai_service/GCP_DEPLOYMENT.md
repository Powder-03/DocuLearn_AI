# Google Cloud Run Deployment Guide

This guide outlines the steps to deploy the DocuLearn AI microservice to Google Cloud Run.

**Recommended Approach**: Connect Cloud Run to your existing Neon (PostgreSQL) and MongoDB Atlas databases.

## Prerequisites

1.  **Google Cloud Project**: Create a project in the [GCP Console](https://console.cloud.google.com/).
2.  **CLI Tools**: Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) and Docker.
3.  **Databases**: Ensure you have connection strings for Neon and MongoDB Atlas.

---

## Automated Deployment

We provide a PowerShell script that handles dependencies, migrations, building, and deploying in one go.

```powershell
./deploy-gcp.ps1
```

---

## Manual Deployment Steps

If you prefer to run the steps manually, follow this guide.

### Step 1: Initial Setup

```bash
# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com
```

### Step 2: Configure Database Access

1.  **Neon PostgreSQL**: Ensure your connection string includes `sslmode=require`. No firewall changes needed for the free tier.
2.  **MongoDB Atlas**: Go to **Network Access** in Atlas and allow `0.0.0.0/0` (since Cloud Run IPs are dynamic).

### Step 3: Store Secrets

Securely store your API keys and database URLs in Google Secret Manager.

```bash
# 1. Neon Database URL
echo -n "YOUR_NEON_CONNECTION_STRING" | gcloud secrets create doculearn-database-url --data-file=-

# 2. MongoDB Atlas URL
echo -n "YOUR_MONGO_CONNECTION_STRING" | gcloud secrets create doculearn-mongodb-url --data-file=-

# 3. Google Gemini API Key
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create doculearn-google-api-key --data-file=-
```

### Step 4: Run Database Migrations

Before deploying code, update the database schema.

```bash
# Install dependencies
pip install -r requirements.txt

# Set local env var for migration (Windows PowerShell example)
$env:DATABASE_URL="YOUR_NEON_CONNECTION_STRING"

# Apply migrations
python -m alembic upgrade head
```

### Step 5: Build and Push Docker Image

1.  **Create Repository** (First time only):
    ```bash
    gcloud artifacts repositories create doculearn-repo --repository-format=docker --location=us-central1
    gcloud auth configure-docker us-central1-docker.pkg.dev
    ```

2.  **Build and Push**:
    ```bash
    IMAGE_URI="us-central1-docker.pkg.dev/YOUR_PROJECT_ID/doculearn-repo/doculearn-ai:latest"
    docker build -t $IMAGE_URI .
    docker push $IMAGE_URI
    ```

### Step 6: Deploy to Cloud Run

Deploy the service and inject the secrets as environment variables.

```bash
gcloud run deploy doculearn-ai-service \
  --image=$IMAGE_URI \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8080 \
  --startup-probe-timeout=600 \
  --startup-probe-failure-threshold=3 \
  --update-secrets=DATABASE_URL=doculearn-database-url:latest \
  --update-secrets=MONGODB_URL=doculearn-mongodb-url:latest \
  --update-secrets=GOOGLE_API_KEY=doculearn-google-api-key:latest \
  --set-env-vars "PLANNING_LLM_MODEL=gemini-2.5-pro,TUTORING_LLM_MODEL=gemini-2.5-flash"
```

### Step 7: Test

Cloud Run will output a Service URL (e.g., `https://doculearn-ai-service-xyz.a.run.app`).

Test the health endpoint:
```bash
curl https://YOUR_SERVICE_URL/
```
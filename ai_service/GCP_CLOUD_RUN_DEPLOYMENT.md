# Google Cloud Run Deployment Guide for DocuLearn AI

This guide outlines two approaches for deploying the DocuLearn AI microservice to Google Cloud Run.

1.  **Simplified Approach (Recommended)**: Uses your existing Neon PostgreSQL and MongoDB Atlas databases. This is faster to set up and more cost-effective.
2.  **Self-Contained Approach**: Uses a new Cloud SQL for PostgreSQL database, keeping all infrastructure within GCP.

---

## Approach 1: Simplified Deployment (Using Existing Databases)

This approach connects your Cloud Run service to your existing Neon and MongoDB databases over the internet.

- **Pros**: Lower cost (no Cloud SQL instance), no data migration required.
- **Cons**: Potential for higher network latency, requires careful security configuration for your databases.

### Prerequisites

1.  **Google Cloud Project**: A new project in the [GCP Console](https://console.cloud.google.com/).
2.  **`gcloud` CLI**: Install and initialize the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
3.  **Docker**: Ensure Docker is running locally.

---

### Deployment Steps

#### Step 1: Initial `gcloud` Setup

```bash
# Log in to your Google Account
gcloud auth login

# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com
```

#### Step 2: Configure Database Firewalls

You must allow your Cloud Run service to connect to your databases.

1.  **Neon PostgreSQL (Free Tier)**:
    -   You are correct that the Neon free tier does not include an IP allowlist feature. It accepts connections from any IP address by default.
    -   No action is required for firewall configuration.
    -   **CRITICAL**: The most important security step is to ensure your Neon connection string includes `sslmode=require`, which is the default for Neon.

2.  **MongoDB Atlas**:
    -   In your Atlas project, navigate to **Network Access**.
    -   Add an IP Address and select **Allow Access From Anywhere** (`0.0.0.0/0`). This is necessary because Cloud Run does not have a static IP by default.

#### Step 3: Store Secrets in Secret Manager

Store your external connection strings and API keys in Secret Manager.

```bash
# 1. Your Neon Database URL
NEON_URL="YOUR_NEON_CONNECTION_STRING"
echo -n $NEON_URL | gcloud secrets create doculearn-database-url --data-file=-

# 2. Your MongoDB Atlas URL
MONGO_URL="YOUR_MONGO_CONNECTION_STRING"
echo -n $MONGO_URL | gcloud secrets create doculearn-mongodb-url --data-file=-

# 3. Your Google Gemini API Key
GEMINI_KEY="YOUR_GEMINI_API_KEY"
echo -n $GEMINI_KEY | gcloud secrets create doculearn-google-api-key --data-file=-
```

#### Step 4: Build and Push Docker Image

1.  **Create an Artifact Registry Repository**:
    ```bash
    gcloud artifacts repositories create doculearn-repo \
      --repository-format=docker \
      --location=us-central1 # Use a region close to your Neon DB
    ```

2.  **Configure Docker**:
    ```bash
    gcloud auth configure-docker us-central1-docker.pkg.dev # Use your region
    ```

3.  **Build, Tag, and Push the Image**:
    ```bash
    # From the ai_service directory
    IMAGE_URI="us-central1-docker.pkg.dev/YOUR_PROJECT_ID/doculearn-repo/doculearn-ai:latest"
    docker build -t $IMAGE_URI .
    docker push $IMAGE_URI
    ```

#### Step 5: Deploy to Cloud Run

Deploy the container, injecting the secrets as environment variables.

```bash
gcloud run deploy doculearn-ai-service \
  --image=${IMAGE_URI} \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8001 \
  --update-secrets=DATABASE_URL=doculearn-database-url:latest \
  --update-secrets=MONGODB_URL=doculearn-mongodb-url:latest \
  --update-secrets=GOOGLE_API_KEY=doculearn-google-api-key:latest
```
- **Note**: The `--add-cloudsql-instances` flag is **not** used in this approach.

#### Step 6: Test Your Deployment

Once deployed, `gcloud` will provide a public URL for your service. Use `curl` or your browser to test the endpoints.

---
---

## Alternative Approach: Self-Contained GCP Deployment (Using Cloud SQL)

This approach creates a new PostgreSQL database within GCP. It offers lower latency and simpler, more secure connectivity at the cost of a running Cloud SQL instance (~$30-50/month).

### Deployment Steps

#### Step 1: Initial `gcloud` Setup
*(Same as above, but enable `sqladmin.googleapis.com`)*
```bash
gcloud services enable sqladmin.googleapis.com
```

#### Step 2: Create Databases

1.  **Cloud SQL (PostgreSQL)**:
    -   Create a new Cloud SQL for PostgreSQL instance (e.g., `db-g1-small`).
    -   Note the **Connection name** (e.g., `your-project:your-region:your-instance`).
    -   Create a database (e.g., `learning_saas_db`) and a user/password.

2.  **MongoDB Atlas**:
    -   Deploy your Atlas cluster in the same GCP region as your Cloud Run service.

#### Step 3: Store Secrets
- For the `DATABASE_URL` secret, use the Cloud SQL Proxy format for secure connections:
  `DB_URL="postgresql+pg8000://USER:PASS@/?unix_socket=/cloudsql/PROJECT:REGION:INSTANCE/.s.PGSQL.5432/DB_NAME"`
  `echo -n $DB_URL | gcloud secrets create doculearn-database-url --data-file=-`

#### Step 4: Run Database Migrations
- Use the **Cloud SQL Auth Proxy** to connect to your new database from your local machine and run `alembic upgrade head`.

#### Step 5: Build and Push Docker Image
*(Same as above)*

#### Step 6: Deploy to Cloud Run
- The deploy command is different. It includes the `--add-cloudsql-instances` flag to create a secure connection to your database.
```bash
gcloud run deploy doculearn-ai-service \
  --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/doculearn-repo/doculearn-ai:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8001 \
  --add-cloudsql-instances=YOUR_INSTANCE_CONNECTION_NAME \
  --update-secrets=DATABASE_URL=doculearn-database-url:latest \
  --update-secrets=MONGODB_URL=doculearn-mongodb-url:latest \
  --update-secrets=GOOGLE_API_KEY=doculearn-google-api-key:latest
```

#### Step 7: Test Your Deployment
*(Same as above)*

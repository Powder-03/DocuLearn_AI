# DocuLearn AI - Google Cloud Run Deployment Script
# Automates the steps in GCP_DEPLOYMENT.md

Write-Host "🚀 DocuLearn AI - Google Cloud Run Deployment" -ForegroundColor Green
Write-Host ""

# --- Configuration ---
$REGION = "us-central1"
$REPO_NAME = "doculearn-repo" # This is the Google Artifact Registry name, NOT your GitHub repo
$IMAGE_NAME = "doculearn-ai"
$SERVICE_NAME = "doculearn-ai-service"

# --- Prerequisites Check ---
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "❌ gcloud CLI not found. Please install Google Cloud SDK." -ForegroundColor Red
    exit 1
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker not found. Please install Docker." -ForegroundColor Red
    exit 1
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python (required for database migrations)." -ForegroundColor Red
    exit 1
}

# Get Project ID
$PROJECT_ID = (gcloud config get-value project 2>$null)
if (-not $PROJECT_ID) {
    Write-Host "❌ No active Google Cloud project found." -ForegroundColor Red
    Write-Host "   Run: gcloud config set project YOUR_PROJECT_ID" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Using Project: $PROJECT_ID" -ForegroundColor Green

# --- Step 1: Install Dependencies ---
Write-Host ""
Write-Host "Step 1: Checking Python dependencies (for migrations)..." -ForegroundColor Cyan
python -m pip install -r requirements.txt | Out-Null
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# --- Step 2: Database Migrations ---
Write-Host ""
Write-Host "Step 2: Running Database Migrations..." -ForegroundColor Cyan

if (-not $env:DATABASE_URL) {
    Write-Host "⚠️  DATABASE_URL environment variable is not set locally." -ForegroundColor Yellow
    Write-Host "   Skipping migrations. Ensure you run 'alembic upgrade head' manually." -ForegroundColor Yellow
} else {
    Write-Host "   Applying migrations to Neon DB..." -ForegroundColor Gray
    python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Migration failed. Check your DATABASE_URL." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Migrations applied successfully" -ForegroundColor Green
}

# --- Step 3: Build and Push ---
Write-Host ""
Write-Host "Step 3: Building and Pushing Container..." -ForegroundColor Cyan

$IMAGE_URI = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME`:latest"

Write-Host "   Building image..." -ForegroundColor Gray
docker build -t $IMAGE_URI .
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "   Pushing image to Artifact Registry..." -ForegroundColor Gray
docker push $IMAGE_URI
if ($LASTEXITCODE -ne 0) { 
    Write-Host "❌ Docker push failed. Ensure you have run: gcloud auth configure-docker $REGION-docker.pkg.dev" -ForegroundColor Red
    exit 1 
}

# --- Step 4: Deploy ---
Write-Host ""
Write-Host "Step 4: Deploying to Cloud Run..." -ForegroundColor Cyan

gcloud run deploy $SERVICE_NAME --image $IMAGE_URI --platform managed --region $REGION --allow-unauthenticated --port 8080 --startup-probe-timeout=600 --startup-probe-failure-threshold=3 --update-secrets="DATABASE_URL=doculearn-database-url:latest,MONGODB_URL=doculearn-mongodb-url:latest,GOOGLE_API_KEY=doculearn-google-api-key:latest" --set-env-vars "PLANNING_LLM_MODEL=gemini-2.5-pro,TUTORING_LLM_MODEL=gemini-2.5-flash"
if ($LASTEXITCODE -ne 0) { 
    Write-Host "❌ Deployment failed." -ForegroundColor Red
    exit 1 
}

Write-Host "✅ Deployment Complete!" -ForegroundColor Green
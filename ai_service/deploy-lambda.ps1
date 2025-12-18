# DocuLearn AI - Quick AWS Lambda Deployment
# Run this script to deploy to AWS Lambda Free Tier

Write-Host "🚀 DocuLearn AI - AWS Lambda Deployment Script" -ForegroundColor Green
Write-Host ""

# Check if AWS CLI is installed
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "   Download from: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found. Please install it first:" -ForegroundColor Red
    Write-Host "   Download from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Prerequisites check passed" -ForegroundColor Green
Write-Host ""

# Configure AWS credentials
Write-Host "Step 1: Configure AWS Credentials" -ForegroundColor Cyan
Write-Host "If you haven't configured AWS CLI yet, run: aws configure" -ForegroundColor Yellow
$configured = Read-Host "Have you configured AWS CLI? (y/n)"
if ($configured -ne "y") {
    Write-Host "Please run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Install Serverless Framework
Write-Host ""
Write-Host "Step 2: Installing Serverless Framework..." -ForegroundColor Cyan
npm install -g serverless
npm install

Write-Host "✅ Serverless Framework installed" -ForegroundColor Green

# Install Python dependencies
Write-Host ""
Write-Host "Step 3: Installing Python dependencies..." -ForegroundColor Cyan
pip install -r requirements-lambda.txt

Write-Host "✅ Python dependencies installed" -ForegroundColor Green

# Deploy to AWS Lambda
Write-Host ""
Write-Host "Step 4: Deploying to AWS Lambda..." -ForegroundColor Cyan
Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow

serverless deploy

Write-Host ""
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Your API endpoint will be shown above." -ForegroundColor Cyan
Write-Host "Test it with:" -ForegroundColor Yellow
Write-Host "  curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/" -ForegroundColor White
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  serverless logs -f api -t" -ForegroundColor White
Write-Host ""
Write-Host "To remove deployment:" -ForegroundColor Yellow
Write-Host "  serverless remove" -ForegroundColor White

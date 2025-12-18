#!/bin/bash
# DocuLearn AI - Quick AWS Lambda Deployment (Linux/Mac)

echo "🚀 DocuLearn AI - AWS Lambda Deployment Script"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"
    echo "   unzip awscliv2.zip"
    echo "   sudo ./aws/install"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install it first:"
    echo "   https://nodejs.org/"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Configure AWS credentials
echo "Step 1: Configure AWS Credentials"
echo "If you haven't configured AWS CLI yet, run: aws configure"
read -p "Have you configured AWS CLI? (y/n) " configured
if [ "$configured" != "y" ]; then
    echo "Please run: aws configure"
    exit 1
fi

# Install Serverless Framework
echo ""
echo "Step 2: Installing Serverless Framework..."
npm install -g serverless
npm install

echo "✅ Serverless Framework installed"

# Install Python dependencies
echo ""
echo "Step 3: Installing Python dependencies..."
pip install -r requirements-lambda.txt

echo "✅ Python dependencies installed"

# Deploy to AWS Lambda
echo ""
echo "Step 4: Deploying to AWS Lambda..."
echo "This may take 5-10 minutes..."

serverless deploy

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "Your API endpoint will be shown above."
echo "Test it with:"
echo "  curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/"
echo ""
echo "To view logs:"
echo "  serverless logs -f api -t"
echo ""
echo "To remove deployment:"
echo "  serverless remove"

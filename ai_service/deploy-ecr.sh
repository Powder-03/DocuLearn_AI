#!/bin/bash

# This script builds the Docker image, pushes it to AWS ECR,
# and deploys the Lambda function using the Serverless Framework.

# --- Configuration ---
# Your AWS Account ID. Find it in the AWS console.
AWS_ACCOUNT_ID="YOUR_AWS_ACCOUNT_ID" 
# The AWS region where you want to deploy.
AWS_REGION="us-east-1"
# The name of your ECR repository. Should match what's in serverless.yml.
ECR_REPOSITORY_NAME="doculearn-ai"
# The name of your service as defined in serverless.yml
SERVICE_NAME="doculearn-ai"

# --- Script ---
set -e # Exit immediately if a command exits with a non-zero status.

echo "Step 1: Logging in to AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "Step 2: Creating ECR repository (if it doesn't exist)..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION > /dev/null 2>&1 || \
    aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION

# Construct the full ECR image URI
IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME"

echo "ECR Image URI: $IMAGE_URI"

echo "Step 3: Building the Docker image..."
# The Serverless Framework can build and push the image automatically.
# The 'serverless.yml' is already configured with the 'provider.ecr.images' section.
# The framework will build the image specified in 'doculearn-app' and tag it appropriately.

echo "Step 4: Deploying with Serverless Framework..."
# The Serverless Framework will handle packaging, pushing to ECR,
# and deploying the Lambda function pointing to the correct image.
serverless deploy --stage prod

echo "✅ Deployment successful!"
echo "Your API should be available at the URL provided in the command output."


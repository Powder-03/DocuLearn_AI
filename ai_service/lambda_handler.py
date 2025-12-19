"""
AWS Lambda handler for the FastAPI application.

This script creates an AWS Lambda handler function that wraps the main FastAPI
application using Mangum, an adapter for running ASGI applications in a
serverless environment.
"""
import os
from mangum import Mangum
from app.main import app

# Set a stage prefix if running on a custom domain
stage = os.environ.get("STAGE", None)
root_path = f"/{stage}" if stage else "/"

# Wrap the FastAPI app with Mangum
handler = Mangum(app, lifespan="off")
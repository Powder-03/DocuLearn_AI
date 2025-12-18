"""
AWS Lambda handler for DocuLearn AI Service
Uses Mangum to wrap FastAPI for Lambda
"""
from mangum import Mangum
from app.main import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")  # Use "off" for Lambda cold starts

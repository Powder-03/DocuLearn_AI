"""
LangServe integration routes
Mounts the LangGraph app as a LangServe endpoint
"""
from fastapi import APIRouter
from langserve import add_routes as langserve_add_routes

from app.graphs.generation_graph import generation_app
from app.graphs.state import GenerationGraphState


def setup_langserve_routes(app):
    """
    Setup LangServe routes for the generation graph.
    
    This function should be called from main.py after app initialization.
    
    The LangServe routes provide:
    - POST /learn/generation/invoke - Synchronous invocation
    - POST /learn/generation/stream - Streaming responses
    - POST /learn/generation/batch - Batch processing
    - GET /learn/generation/playground - Interactive testing UI
    """
    langserve_add_routes(
        app,
        generation_app,
        path="/learn/generation",
        input_type=GenerationGraphState,
        config_keys=["configurable"],
        enabled_endpoints=["invoke", "stream", "playground"]
    )

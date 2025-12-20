import os
from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from app.core.config import settings

# Set environment variable for Google API key
os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY


@lru_cache(maxsize=10)
def get_llm(model_provider: str, model_name: str, temperature: float = 0.7) -> BaseChatModel:
    """
    Factory function to get an LLM instance based on provider and model name.
    
    Args:
        model_provider: "google"
        model_name: The specific model name (e.g., "gemini-1.5-flash")
        temperature: Temperature setting for the model (default 0.7)
    
    Returns:
        BaseChatModel: An instance of the requested LLM
    """
    provider = model_provider.lower()
    if provider == "google":
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_tokens=8192,
            timeout=60,
            max_retries=2,
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}. Use 'google'.")

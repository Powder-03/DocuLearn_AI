import os
from functools import lru_cache
from langchain_groq import ChatGroq
from langchain_core.language_models import BaseChatModel
from app.core.config import settings


# Set environment variable for Groq API key
os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY


@lru_cache(maxsize=10)
def get_llm(model_provider: str, model_name: str, temperature: float = 0.7) -> BaseChatModel:
    """
    Factory function to get an LLM instance based on provider and model name.
    
    Args:
        model_provider: "groq" (primary provider)
        model_name: The specific model name (e.g., "llama-3.1-70b-versatile")
        temperature: Temperature setting for the model (default 0.7)
    
    Returns:
        BaseChatModel: An instance of the requested LLM
    """
    if model_provider.lower() == "groq":
        return ChatGroq(
            model=model_name,
            temperature=temperature,
            max_tokens=8192,
            timeout=60,
            max_retries=2
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}. Use 'groq'.")

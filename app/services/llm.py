import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama

load_dotenv()

def get_llm(provider: str = None, model_name: str = None, **kwargs):
    """
    LLM Factory Function.
    Returns the corresponding ChatModel instance based on the provider.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()
    model_name = model_name or os.getenv("LLM_MODEL_NAME", "gpt-4-turbo")
    
    # Inject default temperature from env if not explicitly passed
    if "temperature" not in kwargs:
        kwargs["temperature"] = float(os.getenv("LLM_TEMPERATURE", 0))

    print(f"🔧 [LLM Factory] Initializing {provider} model: {model_name}")

    if provider == "openai":
        # Supports OpenAI and any OpenAI-compatible API (via OPENAI_API_BASE)
        return ChatOpenAI(model=model_name, **kwargs)
        
    elif provider == "anthropic":
        return ChatAnthropic(model=model_name, **kwargs)
        
    elif provider == "deepseek":
        return ChatDeepSeek(model=model_name, **kwargs)
        
    elif provider == "ollama":
        # Ollama runs locally, no API key needed, but base_url might be required
        return ChatOllama(model=model_name, **kwargs)
        
    else:
        raise ValueError(f"[ERROR] Unsupported LLM Provider: {provider}. "
                         f"Please choose from ['openai', 'anthropic', 'deepseek', 'ollama']")

# Module-level initialization
# This allows other files to simply do: from app.services.llm import llm
llm = get_llm()
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import ChatOllama

load_dotenv()

def get_llm(provider: str = None, model_name: str = None, **kwargs):
    provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()
    model_name = model_name or os.getenv("LLM_MODEL_NAME", "gpt-4-turbo")
    
    if "temperature" not in kwargs:
        kwargs["temperature"] = float(os.getenv("LLM_TEMPERATURE", 0))

    print(f"[LLM Factory] Initializing {provider} model: {model_name}")

    if provider == "openai":
        base_url = os.getenv("OPENAI_API_BASE")
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(model=model_name, **kwargs)
        
    elif provider == "anthropic":
        base_url = os.getenv("ANTHROPIC_API_BASE")
        if base_url:
            kwargs["base_url"] = base_url
        return ChatAnthropic(model=model_name, **kwargs)
        
    elif provider == "deepseek":
        # Support custom base_url for DeepSeek proxies or official API
        base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
        kwargs["base_url"] = base_url
        # ChatDeepSeek uses DEEPSEEK_API_KEY from env automatically
        return ChatDeepSeek(model=model_name, **kwargs)
        
    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        kwargs["base_url"] = base_url
        return ChatOllama(model=model_name, **kwargs)
        
    else:
        raise ValueError(f"[ERROR] Unsupported LLM Provider: {provider}. "
                         f"Please choose from ['openai', 'anthropic', 'deepseek', 'ollama']")

# Module-level initialization
# This allows other files to simply do: from app.services.llm import llm
llm = get_llm()
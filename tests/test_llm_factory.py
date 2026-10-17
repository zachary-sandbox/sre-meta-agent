import os
import pytest
from unittest.mock import patch
from app.services.llm import get_llm
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

@patch.dict(os.environ, {"LLM_PROVIDER": "ollama", "LLM_MODEL_NAME": "qwen2.5:7b"})
def test_factory_returns_ollama():
    """Test if factory returns ChatOllama when env is set to ollama."""
    llm = get_llm()
    assert isinstance(llm, ChatOllama)
    assert llm.model == "qwen2.5:7b"

@patch.dict(os.environ, {"LLM_PROVIDER": "openai", "LLM_MODEL_NAME": "gpt-4-turbo"})
def test_factory_returns_openai():
    """Test if factory returns ChatOpenAI when env is set to openai."""
    llm = get_llm()
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4-turbo"
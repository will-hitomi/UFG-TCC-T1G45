# src/llm/llm_client.py
import os
from pydantic import SecretStr
from langchain_openai import ChatOpenAI

from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]  # .../TCPOPAI
load_dotenv(ROOT / ".env")

def get_llm(temperature: float = 0.2, max_tokens: int = 700):
    base_url = os.getenv("LLM_BASE_URL")   # ex: https://api.mistral.ai/v1
    api_key_raw = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")

    if not base_url:
        raise ValueError("LLM_BASE_URL não definido")
    if not api_key_raw:
        raise ValueError("LLM_API_KEY não definido")
    if not model:
        raise ValueError("LLM_MODEL não definido")

    api_key = SecretStr(api_key_raw)

    # Alguns backends OpenAI-like rejeitam campos de limite de tokens.
    # Mantemos assinatura com max_tokens por compatibilidade, sem enviá-lo.
    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        timeout=60,
    )

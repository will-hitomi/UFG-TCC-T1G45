import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

def get_llm(temperature: float = 0.2):

    return ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
        temperature=temperature,
        timeout=60,
        default_headers={
            "CF-Access-Client-Id": os.getenv("CF_ACCESS_CLIENT_ID"),
            "CF-Access-Client-Secret": os.getenv("CF_ACCESS_CLIENT_SECRET"),
        },
    )

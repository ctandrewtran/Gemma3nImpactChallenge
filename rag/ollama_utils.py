import requests
from typing import List

OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "gemma:3n"


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding for the given text using Ollama's embedding model.
    """
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": EMBED_MODEL, "prompt": text}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"[Ollama] Embedding error: {e}")
        return []


def run_gemma3n(prompt: str) -> str:
    """
    Run a prompt through Gemma 3n via Ollama and return the response.
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {"model": LLM_MODEL, "prompt": prompt}
    try:
        response = requests.post(url, json=payload, stream=False)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        print(f"[Ollama] LLM error: {e}")
        return "[Error: LLM unavailable]" 
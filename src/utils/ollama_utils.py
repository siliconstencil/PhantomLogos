import ollama
from typing import Optional

_client: Optional[ollama.AsyncClient] = None

def get_ollama_client() -> ollama.AsyncClient:
    """
    Returns a singleton instance of ollama.AsyncClient to prevent socket leaks.
    """
    global _client
    if _client is None:
        _client = ollama.AsyncClient()
    return _client

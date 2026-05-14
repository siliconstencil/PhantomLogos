import ollama

_client: ollama.AsyncClient | None = None


def get_ollama_client() -> ollama.AsyncClient:
    """
    Returns a singleton instance of ollama.AsyncClient to prevent socket leaks.
    """
    global _client
    if _client is None:
        import os

        _client = ollama.AsyncClient(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    return _client

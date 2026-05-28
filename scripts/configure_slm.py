import sys

# Add .venv site-packages if needed
try:
    from superlocalmemory.core.config import EmbeddingConfig, LLMConfig, SLMConfig
    from superlocalmemory.storage.models import Mode
except ImportError as exc:
    print(f"Error: Could not import superlocalmemory. Detail: {exc}")
    sys.exit(1)


def main() -> None:
    print("Loading existing config...")
    config = SLMConfig.load()

    print(
        f"Current configuration: mode={config.mode.value}, provider={config.llm.provider}, embedding_model={config.embedding.model_name}"
    )

    # Configure B Mode
    config.mode = Mode.B

    # Create new instances of frozen configs
    new_llm = LLMConfig(provider="ollama", model="llama3.2", api_base="http://localhost:11434")

    new_embedding = EmbeddingConfig(
        provider="ollama",
        model_name="nomic-embed-text-v2-moe-q8:latest",
        ollama_model="nomic-embed-text-v2-moe-q8:latest",
        ollama_base_url="http://localhost:11434",
        dimension=768,
    )

    config.llm = new_llm
    config.embedding = new_embedding

    print("Saving updated configuration...")
    config.save(mode_change=True)

    # Verify by loading again
    verified = SLMConfig.load()
    print(
        f"Verified configuration: mode={verified.mode.value}, provider={verified.llm.provider}, embedding_model={verified.embedding.model_name}, dim={verified.embedding.dimension}"
    )
    print("SLM configured successfully.")


if __name__ == "__main__":
    main()

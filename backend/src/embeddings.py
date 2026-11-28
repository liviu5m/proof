from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, cast


class EmbeddingProvider:
    """Local embedding provider using sentence-transformers.

    Lazy-loads model on first use. Thread-safe singleton via get_embedding_provider().
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model: Any = None

    def _get_cache_dir(self) -> str:
        """Get writable cache directory."""
        # Try env var first
        env_cache = os.getenv("SENTENCE_TRANSFORMERS_HOME")
        if env_cache:
            return env_cache

        # Try /app/.cache (Docker)
        docker_cache = Path("/app/.cache")
        try:
            docker_cache.mkdir(parents=True, exist_ok=True)
            # Test write permission
            test_file = docker_cache / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            return str(docker_cache)
        except (OSError, PermissionError):
            pass

        # Fallback to temp directory (always writable)
        temp_cache = Path(tempfile.gettempdir()) / "sentence_transformers_cache"
        temp_cache.mkdir(parents=True, exist_ok=True)
        return str(temp_cache)

    def _load(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            cache_dir = self._get_cache_dir()
            self._model = SentenceTransformer(self.model_name, cache_folder=cache_dir)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Synchronous embedding - blocks event loop."""
        self._load()
        return cast(
            list[list[float]], self._model.encode(texts, convert_to_numpy=True).tolist()
        )

    async def aembed(self, texts: list[str]) -> list[list[float]]:
        """Async embedding - runs in threadpool to avoid blocking."""
        return await asyncio.to_thread(self.embed, texts)


_embedding_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Get singleton embedding provider instance."""
    global _embedding_provider
    if _embedding_provider is None:
        _embedding_provider = EmbeddingProvider()
    return _embedding_provider

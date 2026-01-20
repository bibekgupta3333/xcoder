"""
Embedding Generation Module

Handles embedding generation using Ollama.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from xcoder import get_logger

logger = get_logger(__name__)


class Embedder:
    """Generate embeddings using Ollama."""

    def __init__(
        self,
        model: str = "nomic-embed-text",
        ollama_url: str = "http://localhost:11434",
        batch_size: int = 10,
    ):
        """
        Initialize Embedder.

        Args:
            model: Embedding model name
            ollama_url: Ollama API URL
            batch_size: Number of texts to embed in parallel
        """
        self.model = model
        self.ollama_url = ollama_url
        self.batch_size = batch_size
        self._client = httpx.AsyncClient(timeout=60.0)

    async def embed(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if failed
        """
        try:
            response = await self._client.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            result = response.json()
            return result.get("embedding")
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    async def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in parallel.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            tasks = [self.embed(text) for text in batch]
            batch_embeddings = await asyncio.gather(*tasks)
            embeddings.extend(batch_embeddings)

        return embeddings

    def embed_sync(self, text: str) -> Optional[List[float]]:
        """
        Synchronous wrapper for embed().

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if failed
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.embed(text))

    def embed_batch_sync(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Synchronous wrapper for embed_batch().

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.embed_batch(texts))

    async def check_model_available(self) -> bool:
        """
        Check if the embedding model is available in Ollama.

        Returns:
            True if model is available
        """
        try:
            response = await self._client.get(f"{self.ollama_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            return any(m.get("name", "").startswith(self.model) for m in models)
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
        await self._client.aclose()

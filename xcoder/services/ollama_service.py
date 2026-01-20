"""
Ollama Service

Handles LLM interactions with Ollama.
"""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from xcoder import get_logger
from xcoder.memory import Message, MessageRole

logger = get_logger(__name__)


class OllamaService:
    """Service for interacting with Ollama LLM."""

    def __init__(
        self,
        model: str = "codellama:7b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """
        Initialize OllamaService.

        Args:
            model: Model name
            base_url: Ollama API base URL
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = httpx.AsyncClient(timeout=120.0)

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = False,
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: User prompt
            system: System prompt
            stream: Stream response

        Returns:
            Generated text
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
            }

            if system:
                payload["system"] = system

            response = await self._client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()

            if stream:
                # Handle streaming response
                full_response = ""
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        full_response += data.get("response", "")
                return full_response
            else:
                result = response.json()
                return result.get("response", "")

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    async def chat(
        self,
        messages: List[Message],
        system: Optional[str] = None,
    ) -> str:
        """
        Chat completion with conversation history.

        Args:
            messages: Conversation messages
            system: System prompt

        Returns:
            Generated response
        """
        try:
            # Convert messages to Ollama format
            ollama_messages = []

            if system:
                ollama_messages.append(
                    {
                        "role": "system",
                        "content": system,
                    }
                )

            for msg in messages:
                ollama_messages.append(
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                    }
                )

            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
            }

            response = await self._client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()

            result = response.json()
            return result.get("message", {}).get("content", "")

        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Streaming chat completion.

        Args:
            messages: Conversation messages
            system: System prompt

        Yields:
            Response chunks
        """
        try:
            # Convert messages to Ollama format
            ollama_messages = []

            if system:
                ollama_messages.append(
                    {
                        "role": "system",
                        "content": system,
                    }
                )

            for msg in messages:
                ollama_messages.append(
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                    }
                )

            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                },
            }

            async with self._client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk

        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.

        Returns:
            List of model information
        """
        try:
            response = await self._client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            result = response.json()
            return result.get("models", [])
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def check_connection(self) -> bool:
        """
        Check if Ollama is accessible.

        Returns:
            True if connected
        """
        try:
            response = await self._client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def pull_model(self, model: str) -> bool:
        """
        Pull a model from Ollama library.

        Args:
            model: Model name

        Returns:
            True if successful
        """
        try:
            response = await self._client.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error pulling model {model}: {e}")
            return False

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    def generate_sync(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Synchronous wrapper for generate().

        Args:
            prompt: User prompt
            system: System prompt

        Returns:
            Generated text
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.generate(prompt, system))

    def chat_sync(self, messages: List[Message], system: Optional[str] = None) -> str:
        """
        Synchronous wrapper for chat().

        Args:
            messages: Conversation messages
            system: System prompt

        Returns:
            Generated response
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.chat(messages, system))
        return loop.run_until_complete(self.chat(messages, system))

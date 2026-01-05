"""Embedding and reranking service using SiliconFlow API.

Uses BGE-M3 for embeddings and BGE-Reranker-V2-M3 for reranking.
"""

import random

import httpx

from app.core.config import get_settings


class EmbeddingService:
    """Service for generating embeddings using SiliconFlow API."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.siliconflow_api_key
        self.base_url = settings.siliconflow_base_url
        self.embedding_model = settings.embedding_model
        self.rerank_model = settings.rerank_model
        self.dimensions = settings.embedding_dimensions

    @property
    def is_available(self) -> bool:
        """Check if the embedding service is available (API key configured)."""
        return bool(self.api_key)

    def _get_headers(self) -> dict[str, str]:
        """Get API headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _generate_mock_embedding(self, text: str) -> list[float]:
        """Generate a deterministic mock embedding for development."""
        # Use hash of text for deterministic random seed
        seed = hash(text) % (2**32)
        rng = random.Random(seed)
        return [rng.uniform(-1, 1) for _ in range(self.dimensions)]

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if not self.is_available:
            return self._generate_mock_embedding(text)
        embeddings = await self.embed_texts([text])
        return embeddings[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        if not self.is_available:
            return [self._generate_mock_embedding(text) for text in texts]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=self._get_headers(),
                json={
                    "model": self.embedding_model,
                    "input": texts,
                    "encoding_format": "float",
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        # Sort by index to maintain order
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> list[dict]:
        """Rerank documents based on query relevance.

        Args:
            query: The search query
            documents: List of document texts to rerank
            top_n: Number of top results to return (default: all)

        Returns:
            List of dicts with 'index', 'document', and 'relevance_score'
        """
        if not documents:
            return []

        if not self.is_available:
            # Return documents in original order with mock scores
            n = top_n or len(documents)
            return [
                {"index": i, "document": doc, "relevance_score": 1.0 - (i * 0.1)}
                for i, doc in enumerate(documents[:n])
            ]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/rerank",
                headers=self._get_headers(),
                json={
                    "model": self.rerank_model,
                    "query": query,
                    "documents": documents,
                    "top_n": top_n or len(documents),
                    "return_documents": True,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        return data.get("results", [])


# Singleton instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

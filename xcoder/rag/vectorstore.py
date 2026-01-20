"""
Vector Store Module

Handles vector database operations using ChromaDB.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from xcoder import get_logger

from .chunker import CodeChunk

logger = get_logger(__name__)


class VectorStore:
    """Manage vector database operations with ChromaDB."""

    def __init__(self, persist_directory: Path, collection_name: str = "code_chunks"):
        """
        Initialize VectorStore.

        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Code chunks for RAG"},
        )

    def add_chunks(
        self,
        chunks: List[CodeChunk],
        embeddings: List[List[float]],
    ) -> int:
        """
        Add code chunks with embeddings to the vector store.

        Args:
            chunks: List of code chunks
            embeddings: List of embedding vectors

        Returns:
            Number of chunks added
        """
        if len(chunks) != len(embeddings):
            logger.error(f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings")
            return 0

        # Filter out chunks with None embeddings
        valid_pairs = [(c, e) for c, e in zip(chunks, embeddings) if e is not None]

        if not valid_pairs:
            logger.warning("No valid chunks with embeddings to add")
            return 0

        chunks, embeddings = zip(*valid_pairs)

        try:
            self.collection.add(
                ids=[chunk.chunk_id for chunk in chunks],
                embeddings=list(embeddings),
                documents=[chunk.content for chunk in chunks],
                metadatas=[
                    {
                        "file_path": chunk.file_path,
                        "chunk_type": chunk.chunk_type,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "language": chunk.language,
                        "hash": chunk.hash,
                        **chunk.metadata,
                    }
                    for chunk in chunks
                ],
            )
            logger.info(f"Added {len(chunks)} chunks to vector store")
            return len(chunks)
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            return 0

    def update_chunks(
        self,
        chunks: List[CodeChunk],
        embeddings: List[List[float]],
    ) -> int:
        """
        Update existing chunks in the vector store.

        Args:
            chunks: List of code chunks
            embeddings: List of embedding vectors

        Returns:
            Number of chunks updated
        """
        if len(chunks) != len(embeddings):
            logger.error(f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings")
            return 0

        valid_pairs = [(c, e) for c, e in zip(chunks, embeddings) if e is not None]

        if not valid_pairs:
            return 0

        chunks, embeddings = zip(*valid_pairs)

        try:
            self.collection.update(
                ids=[chunk.chunk_id for chunk in chunks],
                embeddings=list(embeddings),
                documents=[chunk.content for chunk in chunks],
                metadatas=[
                    {
                        "file_path": chunk.file_path,
                        "chunk_type": chunk.chunk_type,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "language": chunk.language,
                        "hash": chunk.hash,
                        **chunk.metadata,
                    }
                    for chunk in chunks
                ],
            )
            logger.info(f"Updated {len(chunks)} chunks in vector store")
            return len(chunks)
        except Exception as e:
            logger.error(f"Error updating chunks: {e}")
            return 0

    def get_by_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            List of chunk records
        """
        try:
            results = self.collection.get(
                where={"file_path": file_path},
                include=["documents", "metadatas", "embeddings"],
            )

            if not results or not results["ids"]:
                return []

            return [
                {
                    "id": id_,
                    "document": doc,
                    "metadata": meta,
                    "embedding": emb,
                }
                for id_, doc, meta, emb in zip(
                    results["ids"],
                    results["documents"],
                    results["metadatas"],
                    results["embeddings"],
                )
            ]
        except Exception as e:
            logger.error(f"Error retrieving chunks for {file_path}: {e}")
            return []

    def delete_by_file(self, file_path: str) -> int:
        """
        Delete all chunks for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            Number of chunks deleted
        """
        try:
            chunks = self.get_by_file(file_path)
            if not chunks:
                return 0

            self.collection.delete(ids=[chunk["id"] for chunk in chunks])
            logger.info(f"Deleted {len(chunks)} chunks for {file_path}")
            return len(chunks)
        except Exception as e:
            logger.error(f"Error deleting chunks for {file_path}: {e}")
            return 0

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search in the vector store.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            filter_dict: Metadata filters

        Returns:
            List of matching chunks
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_dict,
                include=["documents", "metadatas", "distances"],
            )

            if not results or not results["ids"]:
                return []

            return [
                {
                    "id": id_,
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                }
                for id_, doc, meta, dist in zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ]
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    def count(self) -> int:
        """Get total number of chunks in the vector store."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error counting chunks: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with statistics
        """
        try:
            total_chunks = self.count()

            # Get all unique file paths
            all_data = self.collection.get(include=["metadatas"])
            file_paths = set(meta.get("file_path", "") for meta in all_data.get("metadatas", []))

            # Count by language
            languages = {}
            for meta in all_data.get("metadatas", []):
                lang = meta.get("language", "unknown")
                languages[lang] = languages.get(lang, 0) + 1

            return {
                "total_chunks": total_chunks,
                "total_files": len(file_paths),
                "languages": languages,
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total_chunks": 0, "total_files": 0, "languages": {}}

    def clear(self) -> bool:
        """Clear all data from the vector store."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Code chunks for RAG"},
            )
            logger.info("Vector store cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False
            logger.error(f"Error clearing vector store: {e}")
            return False

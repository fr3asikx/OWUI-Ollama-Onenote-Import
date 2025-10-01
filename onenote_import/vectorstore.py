"""Persistent vector store management using ChromaDB."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


@dataclass
class VectorStoreManager:
    persist_directory: Path
    collection_name: str = "onenote-sections"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    def __post_init__(self) -> None:
        self.persist_directory = Path(self.persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(is_persistent=True),
        )
        self._collection = self._client.get_or_create_collection(self.collection_name)
        self._embedder = SentenceTransformer(self.embedding_model)

    @property
    def collection(self) -> Collection:
        return self._collection

    def _ensure_unique_id(self, document_id: str) -> str:
        # Chroma requires unique ids; reuse the same id to upsert documents.
        return document_id

    def add_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        document_id = self._ensure_unique_id(document_id)
        embedding = self._embedder.encode([text])[0]
        if metadata is None:
            metadata = {}
        self._collection.upsert(
            ids=[document_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
        )


__all__ = ["VectorStoreManager"]

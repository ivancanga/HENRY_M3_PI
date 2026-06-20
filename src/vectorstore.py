from __future__ import annotations

from typing import Any

from src.config import CHROMA_DIR


class VectorStore:
    """Abstracción del vector store por dominio.

    Encapsula el proveedor concreto (hoy Chroma) detrás de una interfaz mínima.
    Para cambiar de proveedor (FAISS, Qdrant, etc.) solo se reescribe esta clase;
    el resto de la aplicación no se entera.
    """

    def __init__(self, domain: str, embeddings: Any) -> None:
        from langchain_chroma import Chroma

        self._store = Chroma(
            collection_name=f"{domain}_docs",
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DIR),
        )

    def is_empty(self) -> bool:
        """True si la colección todavía no tiene documentos indexados."""
        return self._store._collection.count() == 0

    def add(self, chunks: list) -> None:
        """Indexa (embebe y persiste) una lista de chunks."""
        self._store.add_documents(chunks)

    def as_retriever(self, k: int):
        """Devuelve un retriever que trae los k chunks más relevantes."""
        return self._store.as_retriever(search_kwargs={"k": k})

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from src.config import DOMAIN_DIRS, get_settings


def load_documents(folder: Path) -> list:
    """Carga los .md/.txt/.csv de una carpeta como Document de LangChain."""
    from langchain_core.documents import Document

    docs = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".csv"}:
            continue
        docs.append(
            Document(
                page_content=path.read_text(encoding="utf-8"),
                metadata={"source": str(path), "file_name": path.name},
            )
        )
    if not docs:
        raise ValueError(f"No hay documentos en {folder}")
    return docs


def split_documents(documents: list) -> list:
    """Parte los documentos en chunks (markdown-aware)."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def count_chunks(domain: str) -> int:
    """Cuenta los chunks de un dominio (validación offline, sin API key)."""
    return len(split_documents(load_documents(DOMAIN_DIRS[domain])))


def build_embeddings():
    """Crea el modelo de embeddings de OpenAI (requiere OPENAI_API_KEY)."""
    settings = get_settings()
    if not settings.has_openai:
        raise RuntimeError("Falta OPENAI_API_KEY para crear embeddings reales.")

    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )


@lru_cache(maxsize=3)
def get_retriever(domain: str):
    """Crea o reusa la colección del dominio (vía VectorStore) y la devuelve como retriever."""
    from src.vectorstore import VectorStore

    settings = get_settings()
    store = VectorStore(domain, build_embeddings())

    if store.is_empty():
        chunks = split_documents(load_documents(DOMAIN_DIRS[domain]))
        if len(chunks) < 50:
            raise ValueError(f"{domain} tiene {len(chunks)} chunks; mínimo esperado: 50")
        store.add(chunks)

    return store.as_retriever(settings.retriever_k)


def retrieve_context(domain: str, query: str) -> tuple[str, list[dict[str, Any]]]:
    """Recupera los chunks relevantes y devuelve (contexto, fuentes)."""
    retriever = get_retriever(domain)
    docs = retriever.invoke(query)

    context_parts = []
    sources = []
    for index, doc in enumerate(docs, start=1):
        source = doc.metadata.get("file_name") or doc.metadata.get("source") or "documento"
        context_parts.append(f"[{index}] {source}\n{doc.page_content}")
        sources.append({"source": source, "content": doc.page_content, "metadata": doc.metadata})

    return "\n\n".join(context_parts), sources

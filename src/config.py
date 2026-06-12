from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


# --- Rutas del proyecto -------------------------------------------------------
# ROOT_DIR es la carpeta raíz del proyecto (HENRY_M3_PI), calculada a partir de
# la ubicación de este archivo: src/config.py -> parents[1] sube hasta la raíz.
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
CHROMA_DIR = ROOT_DIR / "chroma_db"

# Mapa intent -> carpeta de documentos. Cada agente especialista usa SOLO su
# carpeta, para no contaminar respuestas con documentos de otro dominio.
DOMAIN_DIRS = {
    "hr": DATA_DIR / "hr_docs",
    "tech": DATA_DIR / "tech_docs",
    "finance": DATA_DIR / "finance_docs",
}


def load_env() -> None:
    """Carga las variables de entorno desde el archivo .env de la raíz.

    Si python-dotenv no está instalado, no rompe: simplemente no carga el .env
    (útil para validar el proyecto en entornos mínimos).
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Configuración central del proyecto (inmutable)."""

    openai_api_key: str
    openai_model: str
    openai_embedding_model: str
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str
    # Parámetros de RAG (valores por defecto; se pueden ajustar acá en un solo lugar).
    # chunk_size 600 / overlap 100 -> ~70 chunks por dominio con nuestros documentos.
    chunk_size: int = 600
    chunk_overlap: int = 100
    retriever_k: int = 4

    @property
    def has_openai(self) -> bool:
        """True solo si hay una API key real (no el placeholder del .env.example)."""
        return bool(self.openai_api_key and self.openai_api_key != "your-key-here")

    @property
    def has_langfuse(self) -> bool:
        """True solo si ambas claves de Langfuse son reales (no placeholders)."""
        return bool(
            self.langfuse_public_key
            and self.langfuse_secret_key
            and self.langfuse_public_key != "pk-lf-xxx"
            and self.langfuse_secret_key != "sk-lf-xxx"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Construye la configuración una sola vez (cacheada) leyendo el entorno."""
    load_env()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
        langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
        langfuse_host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )

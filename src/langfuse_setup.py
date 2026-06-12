from __future__ import annotations

from functools import lru_cache
from typing import Any

from src.config import get_settings


TRACE_NAME = "henry-m3-multiagent-rag"


@lru_cache(maxsize=1)
def _get_client():
    """Inicializa una vez el cliente Langfuse (None si faltan credenciales)."""
    settings = get_settings()
    if not settings.has_langfuse:
        return None
    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception:
        return None


def get_langfuse_callback() -> Any | None:
    """Devuelve el CallbackHandler de Langfuse, o None si no hay credenciales."""
    if _get_client() is None:
        return None
    try:
        from langfuse.langchain import CallbackHandler

        return CallbackHandler(public_key=get_settings().langfuse_public_key)
    except Exception:
        return None


def graph_config() -> dict[str, Any]:
    """Config con el callback de Langfuse para graph.invoke ({} si no hay tracing)."""
    callback = get_langfuse_callback()
    if callback is None:
        return {}
    return {
        "callbacks": [callback],
        "run_name": TRACE_NAME,
        "metadata": {"project": "HENRY_M3_PI", "trace_name": TRACE_NAME},
    }


def score_current_trace(scores: dict[str, float], comment: str) -> None:
    """Registra los scores del evaluator en la traza activa (best-effort)."""
    client = _get_client()
    if client is None:
        return
    try:
        for name, value in scores.items():
            client.score_current_trace(name=name, value=value, comment=comment)
    except Exception:
        return

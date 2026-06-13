from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.config import get_settings
from src.langfuse_setup import score_current_trace


class Evaluation(BaseModel):
    """Score estructurado de la calidad de una respuesta (escala 1-10)."""

    relevance: int = Field(ge=1, le=10, description="Qué tanto responde a la pregunta.")
    completeness: int = Field(ge=1, le=10, description="Qué tan completa es.")
    accuracy: int = Field(ge=1, le=10, description="Qué tan soportada está por el contexto.")
    clarity: int = Field(ge=1, le=10, description="Qué tan clara y entendible es.")
    overall: float = Field(ge=1, le=10, description="Score general.")
    feedback: str = Field(description="Comentario cualitativo breve.")


def evaluate(state: dict[str, Any]) -> Evaluation:
    """Evalúa la respuesta con un LLM-as-judge (escala 1-10)."""
    settings = get_settings()
    if not settings.has_openai:
        return Evaluation(
            relevance=6,
            completeness=5,
            accuracy=6,
            clarity=7,
            overall=6.0,
            feedback="Evaluación local simple: configurar OPENAI_API_KEY para score real.",
        )

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Evaluá la respuesta de un sistema RAG de 1 a 10 en relevance, completeness, "
                "accuracy, clarity y overall. Si la respuesta inventa información que no está "
                "en el contexto, bajá accuracy. Devolvé salida estructurada.",
            ),
            (
                "human",
                "Consulta:\n{query}\n\nIntent:\n{intent}\n\nContexto:\n{context}\n\nRespuesta:\n{answer}",
            ),
        ]
    )
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    ).with_structured_output(Evaluation)
    return (prompt | llm).invoke(state)


def evaluator_node(state: dict[str, Any]) -> dict[str, Any]:
    """Nodo evaluator: puntúa la respuesta y registra los scores en Langfuse."""
    evaluation = evaluate(state)
    score_current_trace(
        {
            "relevance": float(evaluation.relevance),
            "completeness": float(evaluation.completeness),
            "accuracy": float(evaluation.accuracy),
            "clarity": float(evaluation.clarity),
            "overall": float(evaluation.overall),
        },
        evaluation.feedback,
    )
    return {"evaluation": evaluation.model_dump()}

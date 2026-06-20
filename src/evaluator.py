from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.config import get_settings
from src.langfuse_setup import score_current_trace


class Evaluation(BaseModel):
    """Score estructurado de calidad del RAG (escala 1-10).

    Las tres dimensiones replican métricas estándar (Ragas/TruLens) que pueden
    calcularse sin respuesta de referencia.
    """

    faithfulness: int = Field(ge=1, le=10, description="Fidelidad de la respuesta al contexto (sin inventar).")
    answer_relevance: int = Field(ge=1, le=10, description="Qué tanto la respuesta aborda la pregunta.")
    context_relevance: int = Field(ge=1, le=10, description="Pertinencia del contexto recuperado (calidad del retriever).")
    overall: float = Field(ge=1, le=10, description="Score general.")
    feedback: str = Field(description="Comentario cualitativo breve.")


def evaluate(state: dict[str, Any]) -> Evaluation:
    """Evalúa la respuesta con un LLM-as-judge (escala 1-10)."""
    settings = get_settings()

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Evaluá la calidad de un sistema RAG de 1 a 10 en tres dimensiones estándar: "
                "faithfulness (la respuesta se apoya únicamente en el contexto; si inventa o usa "
                "conocimiento externo, bajá el score), answer_relevance (la respuesta aborda "
                "directamente la pregunta) y context_relevance (los fragmentos recuperados son "
                "pertinentes a la pregunta). Devolvé también un overall y un feedback breve. "
                "Salida estructurada.",
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
            "faithfulness": float(evaluation.faithfulness),
            "answer_relevance": float(evaluation.answer_relevance),
            "context_relevance": float(evaluation.context_relevance),
            "overall": float(evaluation.overall),
        },
        evaluation.feedback,
    )
    return {"evaluation": evaluation.model_dump()}

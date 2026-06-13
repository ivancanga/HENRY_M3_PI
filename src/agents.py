from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

from src.config import get_settings
from src.rag import retrieve_context


Intent = Literal["hr", "tech", "finance", "unknown"]


class AgentState(TypedDict):
    """Estado compartido que viaja por el grafo."""

    query: str
    intent: str
    reason: str
    context: str
    sources: list[dict[str, Any]]
    answer: str
    evaluation: dict[str, Any]


class RouteDecision(BaseModel):
    """Salida estructurada del router."""

    intent: Intent = Field(description="Dominio elegido: hr, tech, finance o unknown.")
    reason: str = Field(description="Motivo breve del ruteo.")


def route_query(query: str) -> RouteDecision:
    """Clasifica la consulta en hr/tech/finance/unknown con el LLM (structured output)."""
    settings = get_settings()
    if not settings.has_openai:
        raise RuntimeError("Falta OPENAI_API_KEY para clasificar la consulta.")

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Clasifica la consulta del usuario en uno de estos dominios: "
                "hr (recursos humanos), tech (soporte de IT), finance (finanzas) o unknown. "
                "Usa unknown si es ambigua, mezcla varios dominios o está fuera de alcance. "
                "Devolvé salida estructurada.",
            ),
            ("human", "{query}"),
        ]
    )
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    ).with_structured_output(RouteDecision)
    return (prompt | llm).invoke({"query": query})


def orchestrator_node(state: AgentState) -> dict:
    """Nodo orquestador: clasifica la query y produce intent + reason."""
    decision = route_query(state["query"])
    return {"intent": decision.intent, "reason": decision.reason}


def answer_with_rag(domain: str, state: AgentState) -> dict:
    """Lógica RAG común a los agentes: retrieval + respuesta del LLM grounded."""
    settings = get_settings()
    context, sources = retrieve_context(domain, state["query"])

    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"Sos un agente especialista de {domain} de una empresa SaaS. "
                "Respondé en español usando únicamente el contexto provisto. "
                "Si el contexto no alcanza, decí que no tenés información suficiente; no inventes.",
            ),
            ("human", "Contexto:\n{context}\n\nConsulta:\n{query}\n\nRespuesta:"),
        ]
    )
    llm = ChatOpenAI(model=settings.openai_model, temperature=0.2, api_key=settings.openai_api_key)
    response = (prompt | llm).invoke({"context": context, "query": state["query"]})
    return {"context": context, "sources": sources, "answer": response.content}


def hr_agent_node(state: AgentState) -> dict:
    return answer_with_rag("hr", state)


def tech_agent_node(state: AgentState) -> dict:
    return answer_with_rag("tech", state)


def finance_agent_node(state: AgentState) -> dict:
    return answer_with_rag("finance", state)


def unknown_node(state: AgentState) -> dict:
    """Responde sin RAG cuando la consulta no pertenece a ningún dominio."""
    return {
        "context": "",
        "sources": [],
        "answer": (
            "No tengo documentación interna suficiente para responder esa consulta. "
            "Puedo ayudarte con RR. HH., soporte técnico (IT) o finanzas."
        ),
    }

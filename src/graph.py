from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.agents import (
    AgentState,
    finance_agent_node,
    hr_agent_node,
    orchestrator_node,
    tech_agent_node,
    unknown_node,
)
from src.evaluator import evaluator_node


def next_node(state: AgentState) -> str:
    """Función de ruteo: según el intent, devuelve a qué nodo ir (solo el nombre)."""
    intent = state.get("intent", "unknown")
    if intent in {"hr", "tech", "finance"}:
        return intent
    return "unknown"


def build_graph():
    """Construye y compila el grafo multi-agente con ruteo condicional."""
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("hr", hr_agent_node)
    graph.add_node("tech", tech_agent_node)
    graph.add_node("finance", finance_agent_node)
    graph.add_node("unknown", unknown_node)
    graph.add_node("evaluator", evaluator_node)

    graph.add_edge(START, "orchestrator")
    graph.add_conditional_edges(
        "orchestrator",
        next_node,
        {"hr": "hr", "tech": "tech", "finance": "finance", "unknown": "unknown"},
    )
    graph.add_edge("hr", "evaluator")
    graph.add_edge("tech", "evaluator")
    graph.add_edge("finance", "evaluator")
    graph.add_edge("unknown", END)
    graph.add_edge("evaluator", END)

    return graph.compile()


def initial_state(query: str) -> AgentState:
    """Estado inicial del grafo para una consulta (todos los campos presentes)."""
    return {
        "query": query,
        "intent": "",
        "reason": "",
        "context": "",
        "sources": [],
        "answer": "",
        "evaluation": {},
    }

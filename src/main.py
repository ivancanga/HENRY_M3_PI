from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import BaseModel, Field, field_validator

from src.agents import route_query
from src.config import DOMAIN_DIRS, ROOT_DIR
from src.graph import build_graph, initial_state
from src.langfuse_setup import flush, graph_config
from src.rag import count_chunks


class UserQuery(BaseModel):
    """Valida y normaliza la consulta entrante antes de procesarla."""

    text: str = Field(min_length=1, max_length=1000)

    @field_validator("text")
    @classmethod
    def not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("La consulta no puede estar vacía.")
        return cleaned


def run_query(query: str) -> dict:
    """Ejecuta una consulta por el grafo (con tracing si hay credenciales)."""
    query = UserQuery(text=query).text
    graph = build_graph()
    config = graph_config()
    state = initial_state(query)
    result = graph.invoke(state, config=config) if config else graph.invoke(state)
    flush()
    return result


def print_result(result: dict) -> None:
    """Imprime el resultado de una consulta de forma legible."""
    print("\n" + "=" * 70)
    print(f"Pregunta: {result['query']}")
    print(f"Intent:   {result.get('intent')}")
    print(f"Razón:    {result.get('reason')}")
    print("\nRespuesta:")
    print(result.get("answer", ""))

    if result.get("sources"):
        print("\nFuentes recuperadas:")
        for source in result["sources"]:
            print(f"  - {source['source']}")

    if result.get("evaluation"):
        print("\nEvaluación:")
        for key, value in result["evaluation"].items():
            print(f"  - {key}: {value}")
    print("=" * 70)


def validate() -> int:
    """Valida chunks por dominio (>=50) y el ruteo contra test_queries.json."""
    print("Chunks por dominio")
    ok = True
    for domain in DOMAIN_DIRS:
        total = count_chunks(domain)
        status = "OK" if total >= 50 else "FALLA"
        print(f"  - {domain}: {total} ({status})")
        ok = ok and total >= 50

    print("\nRouting con test_queries.json")
    queries = json.loads((ROOT_DIR / "test_queries.json").read_text(encoding="utf-8"))
    aciertos = 0
    for item in queries:
        decision = route_query(item["query"])
        passed = decision.intent == item["expected_intent"]
        aciertos += passed
        ok = ok and passed
        status = "OK" if passed else "FALLA"
        print(f"  - [{status}] esperado={item['expected_intent']:8} detectado={decision.intent:8} | {item['query']}")

    print(f"\nRouting: {aciertos}/{len(queries)} correctos")
    return 0 if ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Sistema multi-agente RAG (HENRY M3)")
    parser.add_argument("--query", "-q", help="Consulta a ejecutar.")
    parser.add_argument("--validate", action="store_true", help="Valida chunks y ruteo.")
    args = parser.parse_args()

    if args.validate:
        raise SystemExit(validate())

    if args.query:
        print_result(run_query(args.query))
        return

    print("Sistema multi-agente RAG. Escribí 'salir' para terminar.")
    while True:
        query = input("\nPregunta: ").strip()
        if query.lower() in {"salir", "exit", "quit"}:
            break
        if query:
            print_result(run_query(query))


if __name__ == "__main__":
    main()

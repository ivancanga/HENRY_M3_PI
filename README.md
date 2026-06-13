# Sistema Multi-Agente RAG con LangGraph

Sistema de routing inteligente para una empresa SaaS que clasifica
automáticamente las consultas entrantes por departamento (RR. HH., Soporte
Técnico, Finanzas) y las deriva a agentes RAG especializados. Un agente
orquestador clasifica la intención de cada consulta y, mediante enrutamiento
condicional con **LangGraph**, delega la respuesta al agente del dominio
correcto, que la fundamenta en la documentación interna de la empresa. Un agente
evaluador puntúa cada respuesta y todo el flujo queda trazado en **Langfuse**
para observabilidad y monitoreo de calidad.

## Arquitectura

```
Usuario pregunta
  → orquestador clasifica la intención (hr / tech / finance / unknown)
  → LangGraph enruta de forma condicional
  → agente RAG especializado recupera contexto de SU dominio (Chroma)
  → el LLM responde usando solo esos documentos (grounded)
  → evaluator puntúa la respuesta (LLM-as-judge)
  → Langfuse traza todo el flujo y registra los scores
```

```
START → orchestrator → [hr | tech | finance] → evaluator → END
                     → unknown → END   (sin RAG ni evaluación)
```

## Estructura del proyecto

```
HENRY_M3_PI/
├── data/                       # Bases de conocimiento (3 dominios, .md)
│   ├── hr_docs/                # ~86 chunks
│   ├── tech_docs/              # ~89 chunks
│   └── finance_docs/           # ~90 chunks
├── src/
│   ├── config.py               # configuración central (claves, rutas, parámetros)
│   ├── rag.py                  # RAG: load → chunk → embeddings → Chroma → retriever
│   ├── agents.py               # router (orquestador) + nodos especialistas
│   ├── evaluator.py            # nodo evaluator (LLM-as-judge)
│   ├── langfuse_setup.py       # observability (callback + scores)
│   ├── graph.py                # grafo LangGraph + ruteo condicional
│   └── main.py                 # CLI (--query, --validate, interactivo)
├── test_queries.json           # 12 consultas de prueba con intención esperada
├── requirements.txt            # dependencias
├── .env.example                # plantilla de variables de entorno
└── README.md
```

## Instalación

### Opción A — con uv (recomendado)

```bash
git clone <repo-url>
cd HENRY_M3_PI
uv sync                 # crea el entorno e instala las dependencias
```

### Opción B — con pip

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configurar las API keys

Copiá la plantilla y completá tus claves:

```bash
cp .env.example .env
```

Editá `.env`:

```env
OPENAI_API_KEY=sk-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com   # o https://us.cloud.langfuse.com
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

- `OPENAI_API_KEY` es necesaria para embeddings, respuestas y evaluación.
- Las claves de Langfuse son opcionales: sin ellas el sistema corre igual, solo
  que no trazea (degradación elegante).

## Cómo ejecutar

Con uv anteponé `uv run`; con pip activá el entorno y usá `python`.

```bash
# Validar el proyecto (cuenta chunks por dominio y chequea el ruteo, sin Chroma)
uv run python -m src.main --validate

# Ejecutar una consulta
uv run python -m src.main --query "¿Cuántos días de vacaciones tengo con 5 años?"

# Modo interactivo (loop hasta escribir 'salir')
uv run python -m src.main
```

> La primera consulta construye las colecciones Chroma (hace embeddings de los
> documentos) y las persiste en `chroma_db/`. Las siguientes corridas las reusan.

### Ejemplo de salida

```
Pregunta: Necesito cambiar mi contraseña del correo corporativo
Intent:   tech
Razón:    La consulta se refiere a un problema de acceso a un sistema de IT.

Respuesta:
No es necesario cambiar tu contraseña a menos que haya sospecha de compromiso...

Fuentes recuperadas:
  - seguridad_contrasenas.md
  - acceso_cuentas.md

Evaluación:
  - relevance: 9
  - completeness: 8
  - accuracy: 9
  - clarity: 10
  - overall: 9.0
```

## Decisiones técnicas

- **LangGraph** para la orquestación: el flujo (clasificar → enrutar → responder
  → evaluar) se modela como un grafo de estado. `add_conditional_edges` implementa
  el enrutamiento condicional según la intención. Se eligió sobre una cadena LCEL
  simple para que el ruteo y los nodos queden explícitos y extensibles.
- **Router con structured output**: el orquestador usa el LLM con
  `with_structured_output(RouteDecision)` (Pydantic), forzando una salida
  `{intent, reason}` validada. Esto hace el ruteo confiable (no parsea texto
  libre) e incluye un intent `unknown` para consultas ambiguas o fuera de dominio.
- **Chroma como vector store**: una colección por dominio, persistida en disco.
  Se eligió sobre FAISS por su persistencia automática y el manejo cómodo de
  colecciones nombradas; a esta escala (~265 chunks) el rendimiento es equivalente.
- **RAG por dominio**: documentos partidos con `RecursiveCharacterTextSplitter`
  (chunk_size 600, overlap 100, separadores markdown-aware), `k=4` chunks por
  consulta. Cada agente busca solo en su colección para no contaminar respuestas.
- **Guardrail anti-alucinación**: el prompt de los agentes obliga a responder solo
  con el contexto recuperado; si no alcanza, lo dice en vez de inventar.
- **Evaluator (LLM-as-judge)**: puntúa relevance, completeness, accuracy, clarity
  y overall (1-10), y envía los scores a Langfuse con la Score API.
- **Observability con Langfuse**: el `CallbackHandler` se pasa en el config del
  grafo y traza automáticamente todo el flujo; los scores del evaluator quedan
  asociados a cada traza para métricas de calidad agregadas.

## Notas de configuración

- Parámetros de RAG (`chunk_size`, `chunk_overlap`, `retriever_k`) y modelos se
  ajustan en un único lugar: `src/config.py`.
- Para reconstruir las colecciones desde cero, borrá la carpeta `chroma_db/`.
- Langfuse 4.x: las credenciales se configuran vía el cliente `Langfuse(...)`; el
  `CallbackHandler` ya no recibe `secret_key`/`host` (los toma del entorno).

## Limitaciones conocidas

- El sistema responde en 3 dominios (HR, Tech, Finance); cualquier otra consulta
  cae en `unknown`.
- Las respuestas dependen de la calidad y cobertura de los documentos en `data/`;
  si la información no está, el agente responde que no la tiene.
- El evaluador es un LLM-as-judge: es una guía de calidad, no un juicio infalible.
- Requiere conexión a internet y una API key de OpenAI con saldo para funcionar
  con RAG real.
```
